import edge_tts
import asyncio
import os
import logging
from pydub import AudioSegment
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

    def _extract_speaker_reference(self, reference_audio, segments, speaker_id, output_path):
        """Extracts a representative clip for a specific speaker."""
        # Find the longest segment for this speaker to get the best quality SE
        speaker_segments = [s for s in segments if s.get("speaker") == speaker_id]
        if not speaker_segments:
            return None
        
        # Sort by duration
        speaker_segments.sort(key=lambda x: x['end'] - x['start'], reverse=True)
        best_seg = speaker_segments[0]
        
        # Extract at least 3-5 seconds if possible, otherwise take what we have
        start = best_seg['start']
        end = best_seg['end']
        
        try:
            audio = AudioSegment.from_file(reference_audio)
            chunk = audio[start*1000 : end*1000]
            chunk.export(output_path, format="wav")
            return output_path
        except Exception as e:
            logger.error(f"Failed to extract reference for {speaker_id}: {e}")
            return None

    def generate_segments(self, segments, output_dir, reference_audio=None):
        """Generates audio for each translated segment, with optional multi-speaker cloning."""
        os.makedirs(output_dir, exist_ok=True)
        cloning_tmp = os.path.join(output_dir, "cloning_tmp")
        os.makedirs(cloning_tmp, exist_ok=True)
        
        speaker_se_map = {}
        source_se = None # Source SE is from the TTS, usually consistent
        
        # Step 1: Pre-extract SE for all unique speakers if cloning is enabled
        if self.cloner and self.cloner.is_available and reference_audio:
            unique_speakers = sorted(list(set(s.get("speaker", "speaker_0") for s in segments)))
            logger.info(f"Detected speakers: {unique_speakers}. Extracting tone colors...")
            
            for spk_id in unique_speakers:
                ref_clip = os.path.join(cloning_tmp, f"ref_{spk_id}.wav")
                if self._extract_speaker_reference(reference_audio, segments, spk_id, ref_clip):
                    logger.info(f"Extracting SE for {spk_id}...")
                    se = self.cloner.extract_se(ref_clip, cloning_tmp)
                    if se is not None:
                        speaker_se_map[spk_id] = se
        
        # Step 2: Generation loop
        for i, segment in enumerate(segments):
            text = segment.get("translated_text", "")
            speaker_id = segment.get("speaker", "speaker_0")
            
            if text:
                base_file = os.path.join(output_dir, f"segment_{i}_base.mp3")
                final_file = os.path.join(output_dir, f"segment_{i}.wav")
                
                # Step 2a: Generate base TTS
                self.generate(text, base_file)
                
                # Step 2b: Optional Cloning
                target_se = speaker_se_map.get(speaker_id)
                if target_se is not None and self.cloner:
                    # Extract source SE from the first successful generation if not already done
                    if source_se is None:
                        source_se = self.cloner.get_audio_se(base_file, cloning_tmp)
                    
                    if source_se is not None:
                        self.cloner.convert(base_file, source_se, target_se, final_file)
                        segment["tts_path"] = final_file
                    else:
                        segment["tts_path"] = base_file
                else:
                    segment["tts_path"] = base_file
                    
        return segments
