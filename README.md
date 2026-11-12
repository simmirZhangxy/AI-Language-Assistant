# Ventuno

一个 Git 仓库，按服务分目录。各服务只改自己的目录。

| 服务 | 放在 | 跑在 |
|------|------|------|
| 语音 + 本地 LLM（App Lab） | [`Keyword-ASR-Local-LLM-Kokoro-TTS/keyword-asr-local-llm-kokoro-tts/`](Keyword-ASR-Local-LLM-Kokoro-TTS/keyword-asr-local-llm-kokoro-tts/) | VENTUNO Q / Arduino App Lab |
| 达妙电机（USB2FDCAN + J4310） | [`services/damiao-motor/`](services/damiao-motor/) | 板子上的 Docker 或本机 Python |
| Pico 固件 | [`pico_sense/`](pico_sense/) | Pico 2 |

公共脚本在 [`scripts/`](scripts/)。达妙完整资料树、可选 SDK 副本放本地 `damiao/`、`third_party/`（已 gitignore，不提交）。

> 克隆后 Kokoro 权重不在 Git 里，见下方「语音助手」。电机运行文件在 `services/damiao-motor/vendor/`。

## 为什么 `git clone` 后缺文件？

根目录 [`.gitignore`](.gitignore) 刻意排除：

- **AI 权重**：`*.onnx`、`*.bin`、`*.pt`、`*.pth` 等（体积大，不宜直接进 Git）
- **本地环境**：`.venv/`、`.env`、`.env.*`
- **构建产物**：`build/`、`.cache/`

因此别人 clone 后，**Kokoro TTS 的 ONNX 模型不会出现在仓库里**；语音助手里的 **LLM / Whisper / 唤醒词** 模型由 **Arduino App Lab 在 VENTUNO Q 上提供**，同样不在本仓库。

## 快速开始（按项目）

### 1. 语音助手（VENTUNO Q + Arduino App Lab）

**硬件**

- VENTUNO Q 开发板
- USB 麦克风、USB 耳机/扬声器（应用内默认 ALSA 输出 `plughw:1,0`，见 `python/main.py`）

**平台**

- 在 VENTUNO Q 上使用 **Arduino App Lab** 打开并部署  
  `Keyword-ASR-Local-LLM-Kokoro-TTS/keyword-asr-local-llm-kokoro-tts/`
- `app.yaml` 中引用的内置 Brick 模型（如 `genie:qwen3_4b_instruct_2507`、`whisper-small-quantized`、唤醒词模型）由平台侧拉取，**无需在本仓库下载**

**必须自行下载：Kokoro 模型（Custom Brick）**

将以下两个文件放到  
`Keyword-ASR-Local-LLM-Kokoro-TTS/keyword-asr-local-llm-kokoro-tts/bricks/kokoro_tts/container/models/`：

| 文件 | 约大小 | 用途 |
|------|--------|------|
| `kokoro-v1.0.fp16.onnx` | ~170 MB | 默认 FP16 推理（与 `KOKORO_MODEL=fp16` 一致） |
| `voices-v1.0.bin` | ~28 MB | 音色嵌入 |

**一键下载（在仓库根目录执行）：**

```bash
./scripts/download-kokoro-models.sh
```

或手动下载（来源：[kokoro-onnx model-files-v1.0](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0)）：

```bash
MODEL_DIR="Keyword-ASR-Local-LLM-Kokoro-TTS/keyword-asr-local-llm-kokoro-tts/bricks/kokoro_tts/container/models"
mkdir -p "$MODEL_DIR"
wget -O "$MODEL_DIR/kokoro-v1.0.fp16.onnx" \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.fp16.onnx
wget -O "$MODEL_DIR/voices-v1.0.bin" \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

Kokoro 容器内的 Python 依赖见  
[`bricks/kokoro_tts/container/requirements.txt`](Keyword-ASR-Local-LLM-Kokoro-TTS/keyword-asr-local-llm-kokoro-tts/bricks/kokoro_tts/container/requirements.txt)  
（`kokoro-onnx`、`onnxruntime` 等）；通过 Custom Brick 的 Docker 构建时会自动 `pip install`。

更多架构说明与 Brick 列表见子项目 [README](Keyword-ASR-Local-LLM-Kokoro-TTS/keyword-asr-local-llm-kokoro-tts/README.md)。

### 2. Pico Sense（Zephyr）

克隆后需要 **West + Zephyr SDK**，依赖由 manifest 从上游拉取，**不会**全部出现在本仓库中。

在项目目录按文档执行即可：

```bash
cd pico_sense
# 见 README：python -m venv、west init、west update、west sdk install 等
```

完整步骤：[pico_sense/README.md](pico_sense/README.md)。

### 3. 达妙电机（Ubuntu 板 + USB2FDCAN + J4310）

克隆后 **`services/damiao-motor/vendor/`** 已包含 aarch64 `libdmcan.so`、Python wheel 与 `damiao.py`。若缺失，在仓库根目录执行：

```bash
./scripts/download-damiao-sdk.sh
```

板子上按 [services/damiao-motor/README.md](services/damiao-motor/README.md)：udev → `dev_sn.py` → `env.example` → `run_j4310_demo.py` 或 `docker compose up --build`。

大型官方 SDK 树可放在本地 **`third_party/`** 或 **`damiao/`**（已在 `.gitignore` 中，不提交）。

## 常见问题

**Docker 构建 Kokoro Brick 失败 / 容器报 `Model ... not found`**  
→ 确认 `container/models/` 下已有上述两个文件后再构建。

**只有代码、没有 VENTUNO Q**  
→ 语音助手无法在普通 PC 上完整复现整条 NPU/Brick 流水线；你仍可参考 `bricks/kokoro_tts` 在 x86 Linux 上单独构建 Kokoro 容器做 TTS 实验。

**想把模型也放进 Git**  
→ 可使用 Git LFS 或 GitHub Release 附件；当前推荐方式为文档 + `download-kokoro-models.sh`，避免仓库体积与 LFS 流量问题。

## 许可证与第三方模型

- Kokoro 权重来自社区 ONNX 发行版（见上方链接），使用前请阅读上游仓库与 [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) 相关许可说明。
- 各子目录代码许可以仓库内现有文件为准（若尚未添加 LICENSE，部署前请自行补充）。
