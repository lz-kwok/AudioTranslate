import os
import sys
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audiotranslate.translator import Translator

class TestTranslator(unittest.TestCase):
    def test_translate_en_zh(self):
        # This will download about 100MB of data for the first time
        translator = Translator(from_code="en", to_code="zh")
        text = "Hello, world! This is a test of the local translation system."
        translated = translator.translate(text)
        
        print(f"\nOriginal: {text}")
        print(f"Translated: {translated}")
        
        self.assertIsInstance(translated, str)
        self.assertGreater(len(translated), 0)

if __name__ == '__main__':
    unittest.main()
