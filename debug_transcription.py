
import os
import sys
import logging
from audiotranslate.transcriber import Transcriber

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)

def debug():
    vocal_path = os.path.join(".translate_workspace", "separated", "htdemucs", "original_audio", "vocals.wav")
    
    if not os.path.exists(vocal_path):
        print(f"Error: {vocal_path} not found.")
        return

    print("Starting full Stage 3 debug...")
    try:
        # We use 'small' as requested in main run
        transcriber = Transcriber(model_size="small", device="cpu")
        
        print("--- Calling transcriber.transcribe(diarize=True) ---")
        segments = transcriber.transcribe(vocal_path, language="en", diarize=True)
        
        print(f"Success! Got {len(segments)} segments.")
        for s in segments[:10]:
            print(f"[{s['start']:.2f}-{s['end']:.2f}] ({s.get('speaker', 'N/A')}): {s['text']}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug()
