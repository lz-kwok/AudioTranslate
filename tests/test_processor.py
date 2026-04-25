import os
import sys
import shutil
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audiotranslate.processor import AudioProcessor

class TestAudioProcessor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = "tests/test_data"
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.input_video = os.path.join(cls.test_dir, "input.mp4")
        
        # Generate a 2-second dummy video with audio
        import ffmpeg
        from static_ffmpeg import add_paths
        add_paths()
        
        try:
            (
                ffmpeg
                .input('sine=frequency=1000:duration=2', f='lavfi')
                .output(cls.input_video, acodec='aac', vcodec='libx264', pix_fmt='yuv420p', f='mp4')
                .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            print(f"Error generating test video: {e.stderr.decode()}")
            raise e

    # @classmethod
    # def tearDownClass(cls):
    #     if os.path.exists(cls.test_dir):
    #         shutil.rmtree(cls.test_dir)

    def test_extract_audio(self):
        processor = AudioProcessor(self.input_video, workspace_dir=self.test_dir)
        output_path = processor.extract_audio("extracted.wav")
        
        self.assertIsNotNone(output_path)
        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(os.path.getsize(output_path) > 0)

if __name__ == '__main__':
    unittest.main()
