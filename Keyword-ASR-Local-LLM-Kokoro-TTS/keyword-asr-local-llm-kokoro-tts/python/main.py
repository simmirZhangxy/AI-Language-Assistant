
import os
import time

import numpy as np
from arduino.app_utils import App, Bridge
from arduino.app_bricks.llm import LargeLanguageModel
from arduino.app_bricks.asr import ASRUnavailableError, AutomaticSpeechRecognition
from arduino.app_peripherals.microphone import (
    BaseMicrophone,
    Microphone,
    MicrophoneReadError,
)
from arduino.app_bricks.keyword_spotting import KeywordSpotting
from kokoro_tts import KokoroTTS
from datetime import datetime
from zoneinfo import ZoneInfo
import urllib.error
import requests
from requests.exceptions import ReadTimeout, ConnectionError

print("=" * 50)
print("🚀 PHASE 1: Loading LOCAL LLM into RAM...")
print("=" * 50)

llm = LargeLanguageModel(
    system_prompt="You are a helpful voice assistant. Keep your answers brief, conversational, and maximum two sentences long. Whenever your answer includes a symbol or unit change it by its word; for example 86% = 86 percent and avoid emojis."
)
llm.with_memory(5)

try:
    print("⏳ Moving ~8GB of data to NPU. Please wait a moment...")
    llm.chat("Respond 'ok'")
    print("✅ Local LLM Loaded.")
except Exception as e:
    print(f"❌ Critical error loading LLM: {e}")

print("\n" + "=" * 50)
print("🎙️ INITIALIZING AUDIO & KOKORO TTS")
print("=" * 50)

# Initialize and warmup Kokoro TTS
tts = KokoroTTS()
print("⏳ Warming Up Kokoro TTS...")
tts.warmup()
print("✅ Kokoro TTS ready.")


class Uac2ArrayMic(BaseMicrophone):
    """UAC2 4-ch @ 48 kHz capture, downmixed to 16 kHz mono for KWS/ASR."""

    _HW_RATE = Microphone.RATE_48K
    _OUT_RATE = Microphone.RATE_16K
    _HW_CHANNELS = 4

    def __init__(self, active_channel: int | None = None):
        self._inner = Microphone(
            device="hw:CARD=UAC2,DEV=0",
            sample_rate=self._HW_RATE,
            channels=self._HW_CHANNELS,
            shared=False,
            buffer_size=Microphone.BUFFER_SIZE_BALANCED,
        )
        self._active_channel = active_channel
        self._sticky_channel: int | None = None
        self._mono48_pending = np.array([], dtype=np.int16)
        super().__init__(
            sample_rate=self._OUT_RATE,
            channels=Microphone.CHANNELS_MONO,
            format=np.int16,
            buffer_size=Microphone.BUFFER_SIZE_BALANCED,
            auto_reconnect=True,
        )
        self.name = "UAC2ArrayMic"

    def _to_mono48(self, chunk: np.ndarray) -> np.ndarray:
        frames = chunk.reshape(-1, self._HW_CHANNELS)
        if frames.size == 0:
            return np.array([], dtype=np.int16)
        if self._active_channel is not None:
            channel = self._active_channel
        else:
            # One live capsule must not be averaged down by the silent ones.
            # Stay on a channel until another is clearly louder.
            energy = np.mean(np.abs(frames.astype(np.int32)), axis=0)
            best = int(np.argmax(energy))
            sticky = self._sticky_channel
            if sticky is None or energy[best] > energy[sticky] * 1.5:
                self._sticky_channel = best
            channel = self._sticky_channel
        return np.ascontiguousarray(frames[:, channel])

    def capture(self) -> np.ndarray | None:
        """Return None while stopped so KWS can exit instead of raising."""
        if not self.is_started():
            return None
        try:
            return super().capture()
        except MicrophoneReadError:
            return None

    def stream(self):
        while self.is_started():
            chunk = self.capture()
            if chunk is not None:
                yield chunk
            elif not self.is_started():
                return
            else:
                time.sleep(0.001)

    def _open_microphone(self) -> None:
        self._mono48_pending = np.array([], dtype=np.int16)
        self._sticky_channel = None
        self._inner.start()

    def _close_microphone(self) -> None:
        self._mono48_pending = np.array([], dtype=np.int16)
        self._inner.stop()

    def _read_audio(self) -> np.ndarray | None:
        chunk = self._inner.capture()
        if chunk is None:
            return None

        self._mono48_pending = np.concatenate(
            (self._mono48_pending, self._to_mono48(chunk))
        )
        need = self.buffer_size * (self._HW_RATE // self._OUT_RATE)
        if len(self._mono48_pending) < need:
            return None

        block = self._mono48_pending[:need]
        self._mono48_pending = self._mono48_pending[need:]
        step = self._HW_RATE // self._OUT_RATE
        return block[::step][: self.buffer_size]


mic = Uac2ArrayMic()
asr = AutomaticSpeechRecognition(mic)
# ASR is started on demand so its asyncio worker is not running while KWS owns the mic.
App.unregister(asr)

app_state = "IDLE"
user_text = ""


def on_keyword_detected():
    global app_state

    print(f"\n🔔 Keyword callback triggered! Current state: {app_state}")

    if app_state == "IDLE":
        print("✨ Wake word 'VENTUNO' detected!")
        app_state = "LISTENING"


spotter = KeywordSpotting(mic=mic, confidence=0.70, debounce_sec=2.0)
spotter.on_detect("Ventuno", on_keyword_detected)


def resume_spotter() -> None:
    """Start keyword spotting again, and reopen the mic if the brick was left half-stopped."""
    App.start_brick(spotter)
    if not mic.is_started():
        spotter.start()


# STATE 0: IDLE
Bridge.call("set_state", 0)
print("\n✅ All systems online! 💤 Listening for 'Ventuno'...")


def loop():
    global app_state, user_text

    if app_state == "IDLE":
        time.sleep(0.1)
        return

    elif app_state == "LISTENING":
        user_text = ""
        partial_text = ""

        # Release KWS workers and mic, then hand the mic to ASR.
        App.stop_brick(spotter)
        mic.start()
        App.start_brick(asr)

        # STATE 1: LISTENING
        Bridge.call("set_state", 1)

        print("\n🟢 ASR ACTIVE: Tell me your command! (Speak now)...")

        try:
            with asr.transcribe_stream(duration=7) as stream:
                for chunk in stream:
                    match chunk.type:
                        case "partial_text":
                            print(
                                f"\r👂 Listening: {chunk.data}",
                                end="",
                                flush=True
                            )
                            partial_text = chunk.data.strip()

                        case "full_text":
                            user_text = chunk.data.strip()
                            break

        except (ReadTimeout, ConnectionError) as e:
            print(f"\n⚠️ Container Connection Timeout: {e}")
            user_text = ""

        except RuntimeError as e:
            print(f"\n⚠️ ASR Container Crashed (Timeout): {e}")
            user_text = ""

        except ASRUnavailableError as e:
            print(f"\n⚠️ ASR service unavailable: {e}")
            user_text = ""

        except Exception as e:
            if partial_text and not user_text:
                user_text = partial_text
            else:
                print(f"\n⚠️ Unexpected ASR Error: {e}")
                user_text = ""

        finally:
            time.sleep(1.5)
            App.stop_brick(asr)
            mic.stop()

        if partial_text and not user_text:
            user_text = partial_text

        if user_text:
            print(f"\n🗣️ You said: {user_text}")

            # STATE 2: PROCESSING
            Bridge.call("set_state", 2)
            app_state = "PROCESSING"

        else:
            print("\n🤷 No command heard or ASR timeout. Returning to sleep...")

            Bridge.call("set_state", 0)
            resume_spotter()
            app_state = "IDLE"
            return

    elif app_state == "PROCESSING":
        print("🧠 AI Thinking (Local): ", end="", flush=True)
        llm_response = ""

        try:
            time_zone = ZoneInfo("America/Santo_Domingo")
            local_time = datetime.now(time_zone)

            # Format the time
            formatted_time = local_time.strftime(
                "%I:%M %p, %A, %B %d, %Y"
            )

            # Build the invisible prompt for context injection
            enriched_prompt = (
                f"[System info: The current local time and date is {formatted_time}]\n\n"
                f"User command: {user_text}"
            )

            for chunk in llm.chat_stream(enriched_prompt):
                print(chunk, end="", flush=True)
                llm_response += chunk

            print()

            time.sleep(0.5)

            if llm_response:
                print("🔊 Speaking via Kokoro...")

                # STATE 3: SPEAKING
                Bridge.call("set_state", 3)

                # Generate audio bytes
                wav_bytes = tts.synth(
                    llm_response,
                    voice="af_heart",
                    speed=1.0,
                    lang="en-us"
                )

                # Save temporary WAV file
                wav_path = "/tmp/assistant_response.wav"
                with open(wav_path, "wb") as f:
                    f.write(wav_bytes)

                # Play audio forcing output to specific hardware
                os.system(f"aplay -D plughw:1,0 {wav_path} -q")

        except (ReadTimeout, ConnectionError, RuntimeError) as e:
            print(f"\n⚠️ Container Error during AI/TTS Processing: {e}")

        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error {e.code}")
            try:
                error_body = e.read().decode("utf-8")
                print(error_body)
            except Exception as parse_error:
                print(f"Couldn't read the error: {parse_error}")

        except Exception as e:
            print(f"\n⚠️ Unexpected LLM/TTS Error: {e}")

        finally:
            print("\n🔄 Returning to sleep mode...")
            Bridge.call("set_state", 0)

            resume_spotter()
            app_state = "IDLE"


try:
    App.run(user_loop=loop)

except KeyboardInterrupt:
    print("\nStopping application...")

finally:
    try:
        App.stop_brick(asr)
    except Exception:
        pass

    try:
        mic.stop()
    except Exception:
        pass

    Bridge.call("set_state", 0)
    # App.run() manages the registered Brick shutdown.
