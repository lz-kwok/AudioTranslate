
from faster_whisper import WhisperModel
import librosa
import soundfile as sf
import os

def test():
    audio_path = ".translate_workspace/separated/htdemucs/original_audio/vocals.wav"
    if not os.path.exists(audio_path):
        print(f"Error: {audio_path} not found.")
        return
        
    print("Loading full audio...")
    y, sr = librosa.load(audio_path, sr=16000)
    test_audio = "test_30s.wav"
    sf.write(test_audio, y, sr)
    
    print("Initializing Whisper (base, float32)...")
    model = WhisperModel("base", device="cpu", compute_type="float32")
    
    print("Transcribing...")
    segments, info = model.transcribe(test_audio, beam_size=2, language="en")
    
    for segment in segments:
        print(f"[{segment.start:.2f} -> {segment.end:.2f}] {segment.text}")
    print("Done!")

if __name__ == "__main__":
    test()
