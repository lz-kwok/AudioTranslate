
import librosa
import numpy as np
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_diarize():
    audio_path = ".translate_workspace/separated/htdemucs/original_audio/vocals.wav"
    
    print("Initializing CAM++...")
    sv_pipeline = pipeline(
        task=Tasks.speaker_verification,
        model='damo/speech_campplus_sv_zh-cn_16k-common'
    )
    
    # Test on first 5 segments of 2 seconds each
    print("Testing extraction on segments...")
    for i in range(5):
        start = i * 2.0
        duration = 2.0
        print(f"Loading segment {i} ({start}s - {start+duration}s)...")
        y, sr = librosa.load(audio_path, sr=16000, offset=start, duration=duration)
        
        print(f"Extracting embedding {i}...")
        import soundfile as sf
        temp_wav = f"temp_seg_{i}.wav"
        sf.write(temp_wav, y, 16000)
        
        print(f"Extracting embedding {i} from {temp_wav}...")
        res = sv_pipeline([temp_wav])
        print(f"Result: {res}")
        emb = res.get("spk_embedding", None)
        print(f"Embedding {i} shape: {emb.shape}")
        
    print("Diarization test done!")

if __name__ == "__main__":
    test_diarize()
