# AudioTranslate 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个全本地化的音视频翻译 CLI 工具，保留背景音。

**Architecture:** 采用模块化流水线架构，使用 Demucs 分离人声，Faster-Whisper 转写，Argos Translate 翻译，Edge-TTS 生成语音，FFmpeg 进行最终合成与语速同步。

**Tech Stack:** Python 3.10, FFmpeg, Demucs, Faster-Whisper, Argos-Translate, Edge-TTS.

---

### Task 1: 项目脚手架与环境配置
**Files:**
- Create: `requirements.txt`
- Create: `setup.py`
- Create: `audiotranslate/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**
```text
faster-whisper
demucs
argostranslate
edge-tts
ffmpeg-python
click
tqdm
```
- [ ] **Step 2: 创建 setup.py 进行包管理**
- [ ] **Step 3: 验证环境安装**
Run: `pip install -r requirements.txt`
- [ ] **Step 4: Commit**
```bash
git add requirements.txt setup.py audiotranslate/
git commit -m "chore: initial project scaffolding"
```

### Task 2: 核心调度器 (Orchestrator) 与 CLI
**Files:**
- Create: `audiotranslate/main.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: 编写 CLI 入口测试**
- [ ] **Step 2: 实现 Click CLI 框架**
- [ ] **Step 3: 验证 --help 命令**
Run: `python -m audiotranslate.main --help`
- [ ] **Step 4: Commit**

### Task 3: 音频预处理 (Preprocessor)
**Files:**
- Create: `audiotranslate/processor.py`
- Create: `tests/test_processor.py`

- [ ] **Step 1: 编写音频提取测试**
- [ ] **Step 2: 实现利用 FFmpeg 提取音轨逻辑**
- [ ] **Step 3: 运行测试验证输出文件存在**
- [ ] **Step 4: Commit**

### Task 4: 人声分离 (Vocal Separation)
**Files:**
- Modify: `audiotranslate/processor.py`
- Create: `tests/test_separation.py`

- [ ] **Step 1: 编写人声分离功能测试**
- [ ] **Step 2: 集成 Demucs 模型加载与推理逻辑**
- [ ] **Step 3: 验证输出 vocals.wav 和 no_vocals.wav**
- [ ] **Step 4: Commit**

### Task 5: 语音识别与时间戳 (Transcription)
**Files:**
- Create: `audiotranslate/transcriber.py`
- Create: `tests/test_transcriber.py`

- [ ] **Step 1: 编写 ASR 功能测试（带时间戳验证）**
- [ ] **Step 2: 集成 Faster-Whisper 推理逻辑**
- [ ] **Step 3: 验证输出 JSON 包含 start, end, text**
- [ ] **Step 4: Commit**

### Task 6: 离线翻译 (Translation)
**Files:**
- Create: `audiotranslate/translator.py`

- [ ] **Step 1: 实现基于 Argos Translate 的离线翻译模块**
- [ ] **Step 2: 验证文本翻译准确性**
- [ ] **Step 3: Commit**

### Task 7: TTS 生成与时长对齐
**Files:**
- Create: `audiotranslate/generator.py`

- [ ] **Step 1: 集成 Edge-TTS 生成语音片段**
- [ ] **Step 2: 实现时长检测逻辑**
- [ ] **Step 3: 集成 FFmpeg atempo 滤镜进行语速同步**
- [ ] **Step 4: Commit**

### Task 8: 最终合成与导出
**Files:**
- Modify: `audiotranslate/main.py`

- [ ] **Step 1: 实现最后的混缩逻辑 (New Vocal + BGM + Original Video)**
- [ ] **Step 2: E2E 集成测试**
- [ ] **Step 3: Commit**
