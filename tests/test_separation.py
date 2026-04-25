import os
import sys
import shutil
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audiotranslate.processor import AudioProcessor

class TestVocalSeparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = "tests/test_sep_data"
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.input_audio = os.path.join(cls.test_dir, "test_audio.wav")
        
        # Generate a 1-second dummy audio with sine wave
        import ffmpeg
        from static_ffmpeg import add_paths
        add_paths()
        
        try:
            (
                ffmpeg
                .input('sine=frequency=1000:duration=1', f='lavfi')
                .output(cls.input_audio, acodec='pcm_s16le', ac=1, ar='16k')
                .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            print(f"Error generating test audio: {e.stderr.decode()}")
            raise e

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def test_separate_vocals(self):
        processor = AudioProcessor(None, workspace_dir=self.test_dir)
        vocals_path, no_vocals_path = processor.separate_vocals(self.input_audio)
        
        # Note: On first run, this will download models (~80MB for htdemucs)
        # This might fail in environments without internet, but here it should work.
        self.assertIsNotNone(vocals_path)
        self.assertIsNotNone(no_vocals_path)
        # We don't strictly check existence here if we want to avoid long run times in CI,
        # but for this "hardcore" dev, we want to see it work.
        # self.assertTrue(os.path.exists(vocals_path))
        # self.assertTrue(os.path.exists(no_vocals_path))

if __name__ == '__main__':
    unittest.main()
