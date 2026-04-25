import os
import sys
import unittest
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audiotranslate.transcriber import Transcriber

class TestTranscriber(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = "tests/test_trans_data"
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.audio_path = os.path.join(cls.test_dir, "hello.wav")
        
        # We need a real audio file with speech for a meaningful test.
        # But for a quick unit test, we can just check if it runs without crashing.
        # Generating a silent audio might result in empty segments.
        import ffmpeg
        from static_ffmpeg import add_paths
        add_paths()
        
        (
            ffmpeg
            .input('sine=frequency=1000:duration=1', f='lavfi')
            .output(cls.audio_path, acodec='pcm_s16le', ac=1, ar='16k')
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )

    def test_transcribe(self):
        # Use 'tiny' for fast testing on CPU
        transcriber = Transcriber(model_size="tiny", device="cpu")
        segments = transcriber.transcribe(self.audio_path, language="en")
        
        # Even with a sine wave, whisper might produce some hallucinations or empty list.
        self.assertIsInstance(segments, list)
        
        # Check saving
        json_path = os.path.join(self.test_dir, "transcription.json")
        transcriber.save_segments(segments, json_path)
        self.assertTrue(os.path.exists(json_path))

if __name__ == '__main__':
    unittest.main()
