import os
import sys
import unittest
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audiotranslate.generator import Generator

class TestGenerator(unittest.TestCase):
    def test_generate_zh(self):
        generator = Generator(voice="zh-CN-XiaoxiaoNeural")
        test_dir = "tests/test_gen_data"
        os.makedirs(test_dir, exist_ok=True)
        
        output_path = os.path.join(test_dir, "test_tts.mp3")
        text = "你好，这是一个本地音频翻译工具的测试。"
        
        result = generator.generate(text, output_path)
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(output_path))
        self.assertGreater(os.path.getsize(output_path), 0)

if __name__ == '__main__':
    unittest.main()
