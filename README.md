# AudioTranslate

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/)

**AudioTranslate** 是一个全本地运行的音视频翻译与自动配音工具。它能够将视频中的人声提取、识别、翻译，并生成全新的配音，同时完美保留原视频的背景音乐与环境音。

[简体中文](README.md) | [English](README_EN.md)

## 🌟 核心特性

- ✅ **人声分离**：采用 Meta 的 Demucs 模型，实现人声与背景音的高精度分离。
- ✅ **多角色识别 (Diarization)**：集成 ModelScope CAM++ 模型，自动区分不同说话人。
- ✅ **全本地化**：支持 Faster-Whisper (转录) 和 Argos Translate (翻译)，无需联网，保护隐私。
- ✅ **背景音保留**：在替换配音的同时，完美保留原片的背景音乐、掌声及环境音。
- ✅ **自动语速对齐**：智能检测翻译后的语速，如果译文过长会自动进行无损加速（atempo），确保语音不重叠且节奏自然。
- ✅ **音色克隆 (High Quality)**：集成 OpenVoice V2，支持提取原视频人物音色并应用到配音中，即使只有几秒素材也能通过自动补齐技术实现稳定克隆。
- ✅ **高质量配音**：集成 Edge-TTS，支持多种极具表现力的磁性男声与柔美女声。

## 🛠️ 技术栈

- **语音识别**: Faster-Whisper
- **角色识别**: ModelScope CAM++ (Diarization)
- **人声分离**: Demucs
- **机器翻译**: Argos Translate (Offline)
- **语音合成**: Edge-TTS & OpenVoice V2
- **音视频处理**: FFmpeg & ffmpeg-python
- **核心框架**: Python, Click, PyTorch

## 🚀 快速开始

### 环境要求

- Python 3.8+
- **FFmpeg**: 系统需安装 FFmpeg 并配置到环境变量。
- **硬件**: 建议 8GB+ 内存，支持 CUDA 的显卡可大幅加速（可选）。

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/your-username/audiotranslate.git
cd audiotranslate

# 安装依赖 (推荐使用虚拟环境)
pip install -r requirements.txt
```

> **注意 (Windows 用户)**:
> 默认的 `requirements.txt` 针对 Windows 上的 PyTorch CPU 兼容性做了优化。如果你有 NVIDIA 显卡，可以自行安装 GPU 版 PyTorch。

### 使用示例

```bash
# 基础用法：将英文视频翻译为中文（默认女声）
python -m audiotranslate.main input.mp4

# 高级用法：使用原视频人物音色进行配音 (需要安装 OpenVoice 并下载权重)
python -m audiotranslate.main input.mp4 --clone

# 高级用法：指定男声、转录模型大小及源语言
python -m audiotranslate.main input.mp4 --target_lang zh --source_lang en --voice zh-CN-YunxiNeural --model_size small
```

#### 参数说明：
- `input_path`: 输入视频或音频路径。
- `-t, --target_lang`: 目标语言（默认 `zh`）。
- `-s, --source_lang`: 源语言（默认 `en`）。
- `--voice`: 指定 TTS 发音人（如 `zh-CN-YunxiNeural` 为磁性男声）。
- `--clone`: 启用音色克隆（需要单独下载 OpenVoice V2 权重）。
- `--diarize`: 开启多角色识别与克隆（自动识别不同说话人并分别克隆）。
- `--model_size`: Whisper 模型大小 (`tiny`, `base`, `small`, `medium`, `large-v3`)。

## 📺 效果对比 (Case Study)

我们以英伟达 GTC 大会黄仁勋的演讲片段为例，展示转换前后的效果对比：

### 原始视频 (English 原声)
https://github.com/lz-kwok/AudioTranslate/raw/main/nvidia-2047718945059156440-01.mp4

*包含 Jensen Huang 的原声及现场背景音。*

### 翻译配音版 (Chinese 汉化)
https://github.com/lz-kwok/AudioTranslate/raw/main/nvidia-2047718945059156440-01_zh.mp4

*替换为磁性男声 (Yunxi)，**背景音完整保留**，并进行了**自动语速对齐**。*

> **提示**：你可以直接下载本项目根目录下的示例视频进行试听对比。

## 📂 项目结构

```text
audiotranslate/
├── audiotranslate/        # 核心逻辑
│   ├── main.py            # CLI 入口
│   ├── processor.py       # 音视频处理与混合 (FFmpeg 逻辑)
│   ├── transcriber.py     # 语音识别 (Whisper)
│   ├── translator.py      # 本地翻译 (Argos)
│   └── generator.py       # 语音合成 (Edge-TTS)
├── tests/                 # 测试用例
├── requirements.txt       # 项目依赖
└── LICENSE                # MIT 许可证
```

## 📝 路线图

- [x] 支持多角色识别与分别配音。
- [ ] 支持更多本地 TTS 引擎（如 Piper, Kokoro-ONNX）。
- [ ] 增加图形化界面 (GUI)。
- [ ] 优化断点续传功能。

## ❓ 常见问题 (FAQ)

**Q: Windows 下安装 Torch 报错或运行 Demucs 闪退？**
A: 这是由于某些版本的 TorchCodec 在 Windows 上存在兼容性问题。本项目 `requirements.txt` 已通过指定 `--index-url` 锁定到稳定的 CPU 版本。如果需要 GPU 加速，请参考 [PyTorch 官网](https://pytorch.org/) 安装对应的 CUDA 版本。

**Q: 翻译效果不理想怎么办？**
A: 本项目使用的是 Argos Translate 本地模型。对于复杂句子，可以尝试调整 `transcriber` 的 `model_size`（如改为 `large-v3`）以获得更准确的转录基础。

**Q: 语音合成的声音可以更换吗？**
A: 可以。通过 `--voice` 参数可以指定 Edge-TTS 支持的所有发音人。启用 `--clone` 后，程序会尝试匹配原声。

## 🎭 音色克隆 (OpenVoice V2)

本项目现已集成 [OpenVoice V2](https://github.com/myshell-ai/OpenVoice)，支持提取原视频中人物的音色（Tone Color）并应用到生成的翻译配音中。

### 启用步骤

1. **准备源码**：
   克隆 OpenVoice 仓库到项目根目录：
   ```bash
   git clone https://github.com/myshell-ai/OpenVoice.git
   ```

2. **下载权重**：
   从 [Hugging Face](https://huggingface.co/myshellai/OpenVoiceV2/tree/main) 下载 `checkpoints_v2` 并解压到项目根目录的 `checkpoints_v2/` 文件夹下。结构如下：
   ```text
   checkpoints_v2/
   └── converter/
       ├── checkpoint.pth
       └── config.json
   ```

3. **运行**：
   在命令中添加 `--clone` 参数：
   ```bash
   python -m audiotranslate.main input.mp4 --clone
   ```

### 兼容性提示 (Windows + Python 3.13)
由于 Python 3.13 移除了 `pkg_resources`，运行 OpenVoice 时可能报错。本项目已在 `requirements.txt` 中锁定了 `setuptools==69.5.1` 以解决此问题。此外，代码已针对无 CUDA 环境进行了自动 CPU 适配。

## 🤝 贡献指南

欢迎提交 Issue 或 Pull Request！
1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 [MIT License](LICENSE)。

---
**免责声明**: 本工具仅供学习交流使用，请勿用于任何非法用途。
