import edge_tts
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

class Generator:
    def __init__(self, voice="zh-CN-XiaoxiaoNeural"):
        self.voice = voice

    async def generate_async(self, text, output_path):
        """Generates audio for a given text using edge-tts."""
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_path)
        return output_path

    def generate(self, text, output_path):
        """Synchronous wrapper for generate_async."""
        if not text.strip():
            return None
        asyncio.run(self.generate_async(text, output_path))
        return output_path

    def generate_segments(self, segments, output_dir):
        """Generates audio for each translated segment."""
        os.makedirs(output_dir, exist_ok=True)
        for i, segment in enumerate(segments):
            text = segment.get("translated_text", "")
            if text:
                out_file = os.path.join(output_dir, f"segment_{i}.mp3")
                self.generate(text, out_file)
                segment["tts_path"] = out_file
        return segments
