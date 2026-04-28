import edge_tts
import asyncio
import os
import logging
from pydub import AudioSegment
from audiotranslate.cloner import VoiceCloner

logger = logging.getLogger(__name__)

# Emotion label → console emoji for readability
_EMOTION_ICON = {
    "excited": "🚀",
    "happy":   "😊",
    "angry":   "😠",
    "sad":     "😢",
    "fearful": "😨",
    "neutral": "😐",
}


class Generator:
    def __init__(self, voice="zh-CN-XiaoxiaoNeural", cloner: VoiceCloner = None):
        self.voice = voice
        self.cloner = cloner

    # ── Core TTS ────────────────────────────────────────────────

    async def generate_async(self, text, output_path,
                             rate="+0%", pitch="+0Hz", volume="+0%",
                             retries=3):
        """Generates audio using edge-tts with optional prosody overrides."""
        for i in range(retries):
            try:
                communicate = edge_tts.Communicate(
                    text,
                    self.voice,
                    rate=rate,
                    pitch=pitch,
                    volume=volume,
                )
                await communicate.save(output_path)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return output_path
            except Exception as e:
                logger.warning(f"TTS generation attempt {i+1} failed for '{text[:30]}...': {e}")
                if i == retries - 1:
                    raise e
                await asyncio.sleep(1)
        return None

    def generate(self, text, output_path,
                 rate="+0%", pitch="+0Hz", volume="+0%"):
        """Synchronous wrapper for generate_async."""
        if not text.strip():
            return None
        try:
            return asyncio.run(
                self.generate_async(text, output_path,
                                    rate=rate, pitch=pitch, volume=volume)
            )
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None

    # ── Speaker reference helpers ────────────────────────────────

    def _extract_speaker_reference(self, reference_audio, segments, speaker_id, output_path):
        """Extracts the longest segment for a specific speaker as reference audio."""
        speaker_segments = [s for s in segments if s.get("speaker") == speaker_id]
        
        # Fallback: if specific speaker not found, pick any segment from the reference
        if not speaker_segments and segments:
            logger.warning(f"Speaker {speaker_id} not found in reference. Falling back to any available speaker.")
            speaker_segments = segments
            
        if not speaker_segments:
            return None
            
        speaker_segments.sort(key=lambda x: x["end"] - x["start"], reverse=True)
        best_seg = speaker_segments[0]
        try:
            audio = AudioSegment.from_file(reference_audio)
            chunk = audio[int(best_seg["start"] * 1000): int(best_seg["end"] * 1000)]
            chunk.export(output_path, format="wav")
            return output_path
        except Exception as e:
            logger.error(f"Failed to extract reference for {speaker_id}: {e}")
            return None

    def _extract_segment_clip(self, reference_audio, start, end, output_path):
        """Extracts one exact segment clip for emotion analysis."""
        try:
            audio = AudioSegment.from_file(reference_audio)
            chunk = audio[int(start * 1000): int(end * 1000)]
            chunk.export(output_path, format="wav")
            return output_path
        except Exception as e:
            logger.debug(f"Clip extraction failed [{start:.1f}s‥{end:.1f}s]: {e}")
            return None

    # ── Main generation loop ─────────────────────────────────────

    def generate_segments(self, segments, output_dir,
                          reference_audio=None, use_emotion=False,
                          reference_segments=None):
        """
        Generates audio for each translated segment.

        Optional features (enabled via flags):
          reference_audio     – enables voice cloning (multi-speaker)
          use_emotion         – enables emotion-aware TTS prosody
          reference_segments  – optional list of original segments to extract speaker SE from
        """
        os.makedirs(output_dir, exist_ok=True)
        cloning_tmp = os.path.join(output_dir, "cloning_tmp")
        os.makedirs(cloning_tmp, exist_ok=True)

        # ── Lazy-import emotion analyzer ────────────────────────
        emotion_analyzer = None
        if use_emotion:
            from audiotranslate.emotion_analyzer import EmotionAnalyzer
            emotion_analyzer = EmotionAnalyzer()
            logger.info("Emotion-aware TTS enabled.")

        # ── Step 1: Pre-extract SE for all unique speakers ──────
        speaker_se_map = {}
        source_se = None

        if self.cloner and self.cloner.is_available and reference_audio:
            # If we have reference segments (e.g. from original diarization), use them for SE extraction
            # instead of using the main segments list (which might be a new script with wrong timestamps).
            se_extraction_source = reference_segments if reference_segments else segments
            
            unique_speakers = sorted(
                set(s.get("speaker", "speaker_0") for s in segments)
            )
            logger.info(f"Detected speakers in script: {unique_speakers}. Extracting tone colors from reference...")
            for spk_id in unique_speakers:
                ref_clip = os.path.join(cloning_tmp, f"ref_{spk_id}.wav")
                if self._extract_speaker_reference(reference_audio, se_extraction_source, spk_id, ref_clip):
                    logger.info(f"Extracting SE for {spk_id}...")
                    se = self.cloner.extract_se(ref_clip, cloning_tmp)
                    if se is not None:
                        speaker_se_map[spk_id] = se

        # ── Step 2: Generation loop ─────────────────────────────
        for i, segment in enumerate(segments):
            text       = segment.get("translated_text", "")
            orig_text  = segment.get("text", "")
            speaker_id = segment.get("speaker", "speaker_0")
            start      = segment.get("start", 0.0)
            end        = segment.get("end",   0.0)

            if not text:
                continue

            base_file  = os.path.join(output_dir, f"segment_{i}_base.mp3")
            final_file = os.path.join(output_dir, f"segment_{i}.wav")

            # — Emotion analysis —
            rate   = "+0%"
            pitch  = "+0Hz"
            volume = "+0%"

            if emotion_analyzer and reference_audio:
                clip_path = os.path.join(cloning_tmp, f"emo_clip_{i}.wav")
                self._extract_segment_clip(reference_audio, start, end, clip_path)
                emo = emotion_analyzer.analyze(clip_path, text)

                rate   = emo["rate"]
                pitch  = emo["pitch"]
                volume = emo["volume"]

                icon = _EMOTION_ICON.get(emo["emotion"], "😐")
                print(
                    f"[Seg {i:03d}] {speaker_id} | "
                    f"{icon} {emo['emotion']:7s} "
                    f"(arousal={emo['arousal']:.2f} valence={emo['valence']:.2f}) | "
                    f"rate: {rate:>5s}  pitch: {pitch:>6s}  vol: {volume:>5s}",
                    flush=True,
                )

            # — Base TTS with emotion prosody —
            self.generate(text, base_file, rate=rate, pitch=pitch, volume=volume)

            # — Optional voice cloning —
            target_se = speaker_se_map.get(speaker_id)
            if target_se is not None and self.cloner:
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
