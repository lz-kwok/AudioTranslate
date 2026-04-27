from faster_whisper import WhisperModel
import os
import json
import logging
import torch
import numpy as np
import librosa
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from sklearn.cluster import AgglomerativeClustering

logger = logging.getLogger(__name__)

class Transcriber:
    def __init__(self, model_size="base", device="cpu", compute_type="float32"):
        """
        Initializes Faster-Whisper model.
        """
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.diarization_pipeline = None

    def transcribe(self, audio_path, language="en", diarize=False):
        """
        Transcribes audio and returns a list of segments with timestamps and optionally speaker labels.
        """
        # We need to compute segments first to use them for memory-efficient diarization
        logger.info(f"Running transcription on {audio_path}...")
        segments_gen, info = self.model.transcribe(audio_path, beam_size=2, language=language)
        
        results = []
        for segment in segments_gen:
            results.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            
        if diarize and results:
            logger.info("Running memory-efficient diarization...")
            diarization_results = self.diarize_segments(audio_path, results)
            if diarization_results:
                # results are already updated in diarize_segments or matched
                results = diarization_results
            
        return results

    def diarize_segments(self, audio_path, transcription_segments):
        """
        Performs speaker diarization by extracting embeddings for each transcription segment.
        This is much more memory efficient than loading the entire audio.
        """
        try:
            print(f"\n--- DIARIZATION DEBUG ---", flush=True)
            if self.diarization_pipeline is None:
                logger.info("Initializing CAM++ Speaker Verification Pipeline...")
                print("DEBUG: Initializing ModelScope Pipeline...", flush=True)
                self.diarization_pipeline = pipeline(
                    task=Tasks.speaker_verification,
                    model='damo/speech_campplus_sv_zh-cn_16k-common'
                )
                logger.info("ModelScope Pipeline initialized.")
                print("DEBUG: ModelScope Pipeline initialized.", flush=True)
            
            embeddings = []
            valid_indices = []
            
            logger.info(f"Extracting embeddings for {len(transcription_segments)} segments...")
            logger.info(f"Loading full audio file (for slicing): {audio_path}")
            # Load full audio once (approx 33MB for 8min 16k mono, very safe)
            full_audio, _ = librosa.load(audio_path, sr=16000)
            logger.info(f"Audio loaded. Total samples: {len(full_audio)}")
            
            for i, seg in enumerate(transcription_segments):
                start_sample = int(seg["start"] * 16000)
                end_sample = int(seg["end"] * 16000)
                y = full_audio[start_sample:end_sample]
                
                if len(y) < 160: # Extremely short
                    continue
                
                import torch
                tensor = torch.FloatTensor(y).unsqueeze(0)
                with torch.no_grad():
                    emb = self.diarization_pipeline.model(tensor)
                    # Convert to numpy and remove batch dim
                    emb = emb.cpu().numpy().flatten()
                
                embeddings.append(emb)
                valid_indices.append(i)
                if i % 10 == 0 or i == len(transcription_segments) - 1:
                    logger.info(f"Processed diarization for segment {i}/{len(transcription_segments)}")
            
            if not embeddings:
                return transcription_segments
                
            embeddings = np.array(embeddings)
            
            # Clustering
            n_samples = len(embeddings)
            n_clusters = None
            if n_samples < 2:
                n_clusters = 1
            
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters, 
                distance_threshold=0.35 if n_clusters is None else None,
                metric='cosine', 
                linkage='average'
            )
            labels = clustering.fit_predict(embeddings)
            
            # Assign labels back to transcription segments
            for i, idx in enumerate(valid_indices):
                transcription_segments[idx]["speaker"] = f"speaker_{labels[i]}"
            
            # Fill in gaps for segments that were too short
            current_speaker = "speaker_0"
            for seg in transcription_segments:
                if "speaker" not in seg:
                    seg["speaker"] = current_speaker
                else:
                    current_speaker = seg["speaker"]
            
            return transcription_segments
            
        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            return transcription_segments

    def _parse_rttm(self, rttm_str):
        """Parses RTTM format if returned by the model."""
        segments = []
        for line in rttm_str.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 8:
                # SPEAKER file 1 <start> <duration> <NA> <NA> <speaker_id> <NA>
                start = float(parts[3])
                duration = float(parts[4])
                speaker = parts[7]
                segments.append({
                    "start": start,
                    "end": start + duration,
                    "speaker": speaker
                })
        return segments

    def match_speakers(self, transcription_segments, diarization_segments):
        """Matches speaker labels to transcription segments based on maximum overlap."""
        for ts in transcription_segments:
            max_overlap = 0
            best_speaker = "speaker_0" # Default
            
            t_start = ts['start']
            t_end = ts['end']
            
            for ds in diarization_segments:
                overlap_start = max(t_start, ds['start'])
                overlap_end = min(t_end, ds['end'])
                overlap = max(0, overlap_end - overlap_start)
                
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = ds['speaker']
            
            ts['speaker'] = best_speaker
            
        return transcription_segments

    def save_segments(self, segments, output_path):
        """Saves segments to a JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(segments, f, ensure_ascii=False, indent=2)
        return output_path
