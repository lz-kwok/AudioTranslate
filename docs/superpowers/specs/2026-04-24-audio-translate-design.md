# AudioTranslate 设计文档

## 1. 项目概述 (Project Overview)
AudioTranslate 是一个开源的 CLI 工具，旨在将视频/音频文件中的语音翻译为目标语言，同时利用 AI 技术保留原始的背景音乐和环境音。该项目专注于全本地化处理，支持 CPU 和 GPU 的自适应切换，确保隐私和无成本运行。

## 2. 核心功能 (Core Features)
- **人声分离**：自动将视频中的人声与背景音轨分离，保留 BGM。
- **本地转写与翻译**：利用本地 Whisper 模型和离线翻译引擎进行处理。
- **高质量 TTS**：生成自然流畅的目标语言语音。
- **智能混缩与同步**：将新语音与原始背景音融合，并自动调整语速以匹配原视频时间轴。
- **硬件自适应**：自动检测 CUDA 环境，无 GPU 时自动降级至 CPU 运行。
- **无干扰输出**：默认不生成硬字幕，专注于音轨替换。

## 3. 技术架构 (Architecture)

### 3.1 模块设计 (Modular Design)
项目采用流水线（Pipeline）模式，分为以下核心组件：
- **`AudioSeparator`**: 使用 `facebook/demucs` (htdemucs) 进行分离。
- **`Transcriber`**: 使用 `Faster-Whisper` 进行 ASR。
- **`Translator`**: 默认为 `Argos Translate` (离线)，支持 `Ollama` 扩展。
- **`VoiceGenerator`**: 
    - **Edge-TTS** (推荐，云端无需 Key，音质极佳)。
    - **Piper** (备选，100% 纯离线，速度极快)。
- **`MediaProcessor`**: 调用 `FFmpeg` 处理音轨提取、时间拉伸（Time-stretch）及最终混缩。

### 3.2 关键数据流 (Data Flow)
1. **输入**：用户提供视频/音频文件。
2. **分离**：输出 `vocals.wav` 和 `bgm.wav`。
3. **识别**：`vocals.wav` -> `segments.json` (包含 start/end/text)。
4. **翻译**：`segments.json` -> `translated.json`。
5. **对齐与合成**：
   - 为每段翻译文本生成 TTS 语音。
   - **语速同步逻辑**：如果生成的 TTS 语音时长超过原片段，使用 `ffmpeg -filter:a "atempo"` 进行压缩对齐，确保不发生音画不同步。
   - 将所有 TTS 片段拼接为完整的翻译音轨。
6. **输出**：合并 `bgm.wav` + `translated_vocal.wav` + `original_video` -> `output.mp4`。

## 4. 硬件建议 (Hardware Requirements)
| 组件 | 推荐显存 (VRAM) | CPU 模式支持 |
|----------|------------------|--------------|
| Demucs | 2GB+ | 支持 |
| Faster-Whisper (Medium) | 4GB+ | 支持 (较慢) |
| 总计建议 | **8GB NVIDIA GPU** | **16GB+ RAM** |

## 5. CLI 接口设计 (CLI Interface)
```bash
audiotranslate <input_path> --target_lang <lang> --output <output_path> [options]
```
参数说明：
- `--target_lang`: 目标语言代码 (如 `zh`, `en`)。
- `--device`: `auto`, `cuda`, `cpu` (默认 `auto`)。
- `--tts_engine`: `edge-tts` 或 `piper` (默认 `edge-tts`)。

## 6. 验证计划 (Verification Plan)
- **同步测试**：验证长句子翻译后语速自动调整的准确性。
- **无显卡测试**：强制使用 `--device cpu` 验证流程完整性。
- **音质测试**：检查混缩后的背景音是否有失真。
