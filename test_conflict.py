
import os
import torch
from faster_whisper import WhisperModel
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

def test_conflict():
    print("Initializing Whisper...")
    w_model = WhisperModel("tiny", device="cpu", compute_type="float32")
    
    print("Initializing ModelScope SV...")
    sv_pipeline = pipeline(
        task=Tasks.speaker_verification,
        model='damo/speech_campplus_sv_zh-cn_16k-common'
    )
    
    print("Both initialized successfully!")

if __name__ == "__main__":
    test_conflict()
