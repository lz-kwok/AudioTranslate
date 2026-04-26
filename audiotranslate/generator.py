import edge_tts
import asyncio
import os
import logging
from audiotranslate.cloner import VoiceCloner

logger = logging.getLogger(__name__)

class Generator:
    def __init__(self, voice="zh-CN-XiaoxiaoNeural", cloner: VoiceCloner = None):
        self.voice = voice
        self.cloner = cloner

    async def generate_async(self, text, output_path, retries=3):
        """Generates audio for a given text using edge-tts with retries."""
        for i in range(retries):
            try:
                communicate = edge_tts.Communicate(text, self.voice)
                await communicate.save(output_path)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return output_path
            except Exception as e:
                logger.warning(f"TTS generation attempt {i+1} failed for '{text[:30]}...': {e}")
                if i == retries - 1:
                    raise e
                await asyncio.sleep(1)
        return None

    def generate(self, text, output_path):
        """Synchronous wrapper for generate_async."""
        if not text.strip():
            return None
        try:
            return asyncio.run(self.generate_async(text, output_path))
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None

    def generate_segments(self, segments, output_dir, reference_audio=None):
        """Generates audio for each translated segment, with optional cloning."""
        os.makedirs(output_dir, exist_ok=True)
        
        target_se = None
        source_se = None
        
        if self.cloner and self.cloner.is_available and reference_audio:
            logger.info("Extracting target tone color from reference audio...")
            target_se = self.cloner.extract_se(reference_audio, os.path.join(output_dir, "cloning_tmp"))
        
        for i, segment in enumerate(segments):
            text = segment.get("translated_text", "")
            if text:
                base_file = os.path.join(output_dir, f"segment_{i}_base.mp3")
                final_file = os.path.join(output_dir, f"segment_{i}.wav")
                
                # Step 1: Generate base TTS
                self.generate(text, base_file)
                
                # Step 2: Optional Cloning
                if target_se is not None and self.cloner:
                    # Extract source SE from the first successful generation if not already done
                    if source_se is None:
                        source_se = self.cloner.get_audio_se(base_file, os.path.join(output_dir, "cloning_tmp"))
                    
                    if source_se is not None:
                        self.cloner.convert(base_file, source_se, target_se, final_file)
                        segment["tts_path"] = final_file
                    else:
                        segment["tts_path"] = base_file
                else:
                    segment["tts_path"] = base_file
                    
        return segments
