# AudioTranslate

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/)

**AudioTranslate** is an all-in-one, fully local video translation and auto-dubbing tool. It extracts, transcribes, and translates human speech from videos, then generates new dubbed audio while perfectly preserving the original background music and ambient sounds.

[简体中文](README.md) | English

## 🌟 Key Features

- ✅ **Vocal Separation**: Uses Meta's Demucs model to achieve high-precision separation of vocals and background noise.
- ✅ **Fully Local**: Powered by Faster-Whisper (transcription) and Argos Translate (translation). No internet connection required, ensuring maximum privacy.
- ✅ **Background Preservation**: Seamlessly replaces the speech while keeping the original BGM, applause, and environmental sounds intact.
- ✅ **Auto Speed Alignment**: Intelligently detects dubbed audio duration. If the translation is longer than the original segment, it applies lossless speed adjustment (`atempo`) to prevent overlapping and maintain natural rhythm.
- ✅ **High-Quality Dubbing**: Integrated with Edge-TTS, supporting a variety of expressive male and female voices.

## 🛠️ Tech Stack

- **Speech-to-Text**: Faster-Whisper
- **Source Separation**: Demucs
- **Machine Translation**: Argos Translate (Offline)
- **Text-to-Speech**: Edge-TTS
- **Audio/Video Processing**: FFmpeg & ffmpeg-python
- **Core Framework**: Python, Click, PyTorch

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- **FFmpeg**: Must be installed and added to your system's PATH.
- **Hardware**: 8GB+ RAM recommended. A CUDA-enabled GPU can significantly speed up processing (optional).

### Installation

```bash
# Clone the repository
git clone https://github.com/lz-kwok/AudioTranslate.git
cd AudioTranslate

# Install dependencies (Virtual environment recommended)
pip install -r requirements.txt
```

> **Note (Windows Users)**:
> The default `requirements.txt` is optimized for PyTorch CPU compatibility on Windows. If you have an NVIDIA GPU, you may want to install the GPU version of PyTorch manually.

### Usage Example

```bash
# Basic usage: Translate English video to Chinese (Default voice)
python -m audiotranslate.main input.mp4

# Advanced usage: Specify male voice, model size, and source language
python -m audiotranslate.main input.mp4 --target_lang zh --source_lang en --voice zh-CN-YunxiNeural --model_size small
```

#### CLI Options:
- `input_path`: Path to the input video or audio file.
- `-t, --target_lang`: Target language (default: `zh`).
- `-s, --source_lang`: Source language (default: `en`).
- `--voice`: Specify the TTS voice (e.g., `zh-CN-YunxiNeural` for a deep male voice).
- `--model_size`: Whisper model size (`tiny`, `base`, `small`, `medium`, `large-v3`).

## 📺 Case Study

Using a segment from NVIDIA GTC (Jensen Huang's keynote) as an example:

### Original Video (English)
<video src="nvidia-2047718945059156440-01.mp4" width="600" controls></video>

*Contains original vocals and live background noise.*

### Translated & Dubbed (Chinese)
<video src="nvidia-2047718945059156440-01_zh.mp4" width="600" controls></video>

*Vocals replaced with a deep male voice (Yunxi). **Background sounds are fully preserved**, and **auto-speed alignment** is applied.*

> **Tip**: You can download the sample videos from the root directory to compare the audio quality directly.

## 📂 Project Structure

```text
audiotranslate/
├── audiotranslate/        # Core logic
│   ├── main.py            # CLI Entry point
│   ├── processor.py       # Audio/Video processing & mixing (FFmpeg logic)
│   ├── transcriber.py     # Speech recognition (Whisper)
│   ├── translator.py      # Local translation (Argos)
│   └── generator.py       # Speech synthesis (Edge-TTS)
├── tests/                 # Unit tests
├── requirements.txt       # Dependencies
└── LICENSE                # MIT License
```

## 📝 Roadmap

- [ ] Support more local TTS engines (e.g., Piper, Kokoro-ONNX).
- [ ] Graphical User Interface (GUI).
- [ ] Speaker diarization and multi-voice support.
- [ ] Checkpoint/Resume functionality for long videos.

## ❓ FAQ

**Q: Installation of Torch failed or Demucs crashed on Windows?**
A: Some TorchCodec versions have compatibility issues on Windows. The `requirements.txt` in this repo is pinned to a stable CPU version via `--index-url`. For GPU acceleration, please refer to [PyTorch.org](https://pytorch.org/) to install the appropriate CUDA version.

**Q: The translation isn't accurate?**
A: This project uses Argos Translate offline models. For complex sentences, try increasing the Whisper `model_size` (e.g., to `large-v3`) to get a better transcription base.

**Q: Can I change the dubbed voice?**
A: Yes. You can specify any voice supported by Edge-TTS using the `--voice` parameter. Run `edge-tts --list-voices` to see the full list of available voices.

## 🤝 Contributing

Contributions are welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the [MIT License](LICENSE).

---
**Disclaimer**: This tool is for educational and research purposes only. Please do not use it for any illegal activities.
