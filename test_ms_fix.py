
import librosa
import torch
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

def test_extraction():
    print("Initializing...")
    sv_pipeline = pipeline(
        task=Tasks.speaker_verification,
        model='damo/speech_campplus_sv_zh-cn_16k-common'
    )
    
    audio_path = ".translate_workspace/separated/htdemucs/original_audio/vocals.wav"
    y, _ = librosa.load(audio_path, sr=16000, offset=0, duration=2.0)
    
    print("Testing pipeline on single input...")
    # Some versions of this pipeline support this:
    try:
        res = sv_pipeline(y)
        print(f"Direct call result keys: {res.keys() if isinstance(res, dict) else 'N/A'}")
    except Exception as e:
        print(f"Direct call failed: {e}")

    print("\nTesting model forward directly...")
    # The most reliable way for Cam++ in ModelScope
    try:
        tensor = torch.FloatTensor(y).unsqueeze(0)
        with torch.no_grad():
            emb = sv_pipeline.model(tensor)
            print(f"Model forward embedding shape: {emb.shape}")
            return True
    except Exception as e:
        print(f"Model forward failed: {e}")
        
    return False

if __name__ == "__main__":
    test_extraction()
