from faster_whisper import WhisperModel
import os
import json

class Transcriber:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        """
        Initializes Faster-Whisper model.
        model_size: tiny, base, small, medium, large-v3
        device: cpu, cuda
        compute_type: int8, float16 (for GPU)
        """
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path, language="en"):
        """
        Transcribes audio and returns a list of segments with timestamps.
        """
        segments, info = self.model.transcribe(audio_path, beam_size=5, language=language)
        
        results = []
        for segment in segments:
            results.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            
        return results

    def save_segments(self, segments, output_path):
        """Saves segments to a JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(segments, f, ensure_ascii=False, indent=2)
        return output_path
