from setuptools import setup, find_packages

setup(
    name="audiotranslate",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "faster-whisper",
        "demucs",
        "argostranslate",
        "edge-tts",
        "ffmpeg-python",
        "click",
        "tqdm",
        "torch",
        "torchaudio",
    ],
    entry_points={
        "console_scripts": [
            "audiotranslate=audiotranslate.main:main",
        ],
    },
    python_requires=">=3.9",
)
