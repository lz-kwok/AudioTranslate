import os
import sys
import unittest
import ffmpeg
from static_ffmpeg import add_paths
add_paths()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audiotranslate.processor import AudioProcessor

class TestMixing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = "tests/test_mix_data"
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.bg_path = os.path.join(cls.test_dir, "background.wav")
        cls.tts1_path = os.path.join(cls.test_dir, "tts1.wav")
        cls.tts2_path = os.path.join(cls.test_dir, "tts2.wav")
        
        # Create background (5s noise)
        (
            ffmpeg
            .input('anoisesrc=d=5', f='lavfi')
            .output(cls.bg_path, acodec='pcm_s16le', ar='16k', ac=1)
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
        
        # Create TTS1 (1s sine at 1s)
        (
            ffmpeg
            .input('sine=f=440:d=1', f='lavfi')
            .output(cls.tts1_path, acodec='pcm_s16le', ar='16k', ac=1)
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
        
        # Create TTS2 (1s sine at 3s)
        (
            ffmpeg
            .input('sine=f=880:d=1', f='lavfi')
            .output(cls.tts2_path, acodec='pcm_s16le', ar='16k', ac=1)
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )

    def test_mixing(self):
        processor = AudioProcessor(None, workspace_dir=self.test_dir)
        segments = [
            {"start": 1.0, "tts_path": self.tts1_path},
            {"start": 3.0, "tts_path": self.tts2_path}
        ]
        
        output_path = os.path.join(self.test_dir, "final_mix.wav")
        result = processor.mix_translated_audio(self.bg_path, segments, output_path)
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(output_path))
        # Check duration (should be ~5s)
        probe = ffmpeg.probe(output_path)
        duration = float(probe['format']['duration'])
        self.assertAlmostEqual(duration, 5.0, delta=0.5)

if __name__ == '__main__':
    unittest.main()
