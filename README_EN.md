# AudioTranslate

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/)

**AudioTranslate** is a fully local audio/video translation and automated dubbing tool. It extracts, transcribes, translates, and generates new dubbing for the human voice in a video while perfectly preserving the original background music and ambient sounds.

[简体中文](README.md) | [English](README_EN.md)

## 🌟 Core Features

- ✅ **Vocal Separation**: Uses Meta's Demucs model for high-precision separation of vocals and background noise.
- ✅ **Speaker Diarization**: Integrated ModelScope CAM++ model to automatically distinguish between different speakers.
- ✅ **Fully Localized**: Supports Faster-Whisper (transcription) and Argos Translate (translation). No internet connection required, ensuring privacy.
- ✅ **Background Preservation**: Perfectly keeps original background music, applause, and environmental sounds while replacing the dubbing.
- ✅ **Auto-Speed Alignment**: Intelligently detects the speed of translated text. If the translation is too long, it performs lossless acceleration (atempo) to ensure no overlap and natural rhythm.
- ✅ **Voice Cloning (High Quality)**: Integrated OpenVoice V2. Supports extracting the tone color of original speakers and applying it to the new dubbing, with stability even for short clips via auto-padding.
- ✅ **Emotion-Aware TTS**: **[NEW]** Integrated a two-layer emotion analyzer (acoustic features + semantic sentiment) to adjust prosody (rate, pitch, volume) via SSML in real-time, making the dubbing sound more "human".
- ✅ **High-Quality Dubbing**: Integrated Edge-TTS, supporting various expressive male and female voices.

## 🛠️ Technical Stack

- **Speech Recognition**: Faster-Whisper
- **Diarization**: ModelScope CAM++
- **Vocal Separation**: Demucs
- **Machine Translation**: Argos Translate (Offline)
- **Speech Synthesis**: Edge-TTS & OpenVoice V2
- **Audio/Video Processing**: FFmpeg & ffmpeg-python
- **Core Framework**: Python, Click, PyTorch

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- **FFmpeg**: Must be installed and added to the system's PATH.
- **Hardware**: 8GB+ RAM recommended. NVIDIA GPU with CUDA support is highly recommended for acceleration.

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/audiotranslate.git
cd audiotranslate

# Install dependencies (Virtual environment recommended)
pip install -r requirements.txt
```

> **Note for Windows Users**:
> The default `requirements.txt` is optimized for stable PyTorch CPU compatibility on Windows. If you have an NVIDIA GPU, please install the GPU version of PyTorch manually.

### Examples

```bash
# Basic usage: Translate English video to Chinese (default female voice)
python -m audiotranslate.main input.mp4

# Advanced: Voice Cloning + Diarization + Emotion Awareness
python -m audiotranslate.main input.mp4 --clone --diarize --emotion

# Advanced: Specify male voice, transcription model size, and languages
python -m audiotranslate.main input.mp4 --target_lang zh --source_lang en --voice zh-CN-YunxiNeural --model_size small
```

#### CLI Parameters:
- `input_path`: Path to the input video or audio.
- `-t, --target_lang`: Target language (default `zh`).
- `-s, --source_lang`: Source language (default `en`).
- `--voice`: Specify TTS voice (e.g., `zh-CN-YunxiNeural`).
- `--clone`: Enable Voice Cloning (requires OpenVoice V2 weights).
- `--diarize`: Enable Multi-speaker Diarization and cloning.
- `--emotion`: Enable Real-time Emotion Awareness.
- `--model_size`: Whisper model size (`tiny`, `base`, `small`, `medium`, `large-v3`).

## 📺 Comparisons (Case Study)

Using Jensen Huang's GTC keynote as an example:

### Original Video (English)
[Link to original video]

### Translated & Dubbed (Chinese)
[Link to dubbed video]

*Replaced with male voice (Yunxi), **background preserved**, and **auto-speed aligned**.*

## 📂 Project Structure

```text
audiotranslate/
├── audiotranslate/        # Core Logic
│   ├── main.py            # CLI Entry
│   ├── processor.py       # A/V Processing (FFmpeg)
│   ├── transcriber.py     # Speech Recognition (Whisper)
│   ├── translator.py      # Local Translation (Argos)
│   ├── generator.py       # Speech Synthesis (Edge-TTS)
│   └── emotion_analyzer.py # Emotion Analysis
├── tests/                 # Unit Tests
├── requirements.txt       # Dependencies
└── LICENSE                # MIT License
```

## 📝 Roadmap

- [x] Multi-speaker Diarization & Cloning.
- [x] Emotion-Aware Dubbing.
- [ ] More local TTS engines (Piper, Kokoro-ONNX).
- [ ] Graphical User Interface (GUI).
- [ ] Optimize resume and caching mechanisms.

## 🎭 Voice Cloning (OpenVoice V2)

This project integrates [OpenVoice V2](https://github.com/myshell-ai/OpenVoice) to extract "Tone Color" from original videos.

### Setup

1. **Clone Source**:
   ```bash
   git clone https://github.com/myshell-ai/OpenVoice.git
   ```

2. **Download Weights**:
   Download `checkpoints_v2` from [Hugging Face](https://huggingface.co/myshellai/OpenVoiceV2/tree/main) and extract to `checkpoints_v2/` in the root directory.

3. **Run**:
   Add `--clone` to your command.

## 🤝 Contributing

Contributions are welcome!
1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## License

This project is licensed under the [MIT License](LICENSE).

---
**Disclaimer**: This tool is for educational and research purposes only. Do not use for illegal activities.
