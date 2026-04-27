import ffmpeg
import os
import subprocess
import sys
import logging

logger = logging.getLogger(__name__)

try:
    from static_ffmpeg import add_paths
    add_paths()
except ImportError:
    pass

class AudioProcessor:
    def __init__(self, input_path, workspace_dir=".temp"):
        self.input_path = input_path
        self.workspace_dir = workspace_dir
        os.makedirs(self.workspace_dir, exist_ok=True)
        
    def extract_audio(self, output_name="original_audio.wav"):
        """Extracts audio from video file using FFmpeg."""
        output_path = os.path.join(self.workspace_dir, output_name)
        
        try:
            # Overwrite if exists
            stream = ffmpeg.input(self.input_path)
            stream = ffmpeg.output(stream, output_path, acodec='pcm_s16le', ac=1, ar='16k')
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            return output_path
        except ffmpeg.Error as e:
            print(f"Error extracting audio: {e.stderr.decode() if e.stderr else str(e)}")
            return None

    def separate_vocals(self, audio_path):
        """Separates vocals from background audio using Demucs."""
        try:
            from demucs.separate import main as demucs_main
            
            output_dir = os.path.join(self.workspace_dir, "separated")
            # Demucs creates a nested structure: output_dir/htdemucs/[filename]/vocals.wav
            filename = os.path.basename(audio_path).split('.')[0]
            vocals_path = os.path.join(output_dir, "htdemucs", filename, "vocals.wav")
            no_vocals_path = os.path.join(output_dir, "htdemucs", filename, "no_vocals.wav")

            if os.path.exists(vocals_path) and os.path.exists(no_vocals_path):
                logger.info(f"Found existing separated vocals at {vocals_path}, skipping Demucs.")
                return vocals_path, no_vocals_path

            os.makedirs(output_dir, exist_ok=True)
            
            # demucs uses sys.argv if no args are passed, so we must pass them explicitly
            args = [
                "-n", "htdemucs",
                "--two-stems", "vocals",
                audio_path,
                "-o", output_dir
            ]
            
            demucs_main(args)
            return vocals_path, no_vocals_path
        except Exception as e:
            print(f"Error separating vocals: {str(e)}")
            return None, None

    def merge_audio_video(self, video_path, audio_path, output_path):
        """Merges new audio with original video."""
        try:
            video = ffmpeg.input(video_path)
            audio = ffmpeg.input(audio_path)
            # Use -c:v copy to keep video stream as is
            ffmpeg.output(video.video, audio.audio, output_path, vcodec='copy', acodec='aac', shortest=None).run(overwrite_output=True)
            return output_path
        except ffmpeg.Error as e:
            print(f"Error merging files: {e.stderr.decode() if e.stderr else str(e)}")
            return None

    def get_duration(self, audio_path):
        """Returns duration of audio file in seconds."""
        try:
            probe = ffmpeg.probe(audio_path)
            return float(probe['format']['duration'])
        except Exception:
            return 0

    def mix_translated_audio(self, background_audio, segments, output_path):
        """
        Mixes background audio with delayed TTS segments.
        Ensures TTS volume is audible while keeping background in place.
        Prevents overlapping by speeding up segments that exceed their allotted time.
        """
        try:
            # Load background
            bg = ffmpeg.input(background_audio)
            
            # If there are no segments, just return background
            if not segments:
                ffmpeg.output(bg, output_path, acodec='pcm_s16le').run(overwrite_output=True)
                return output_path

            # Group all TTS segments
            tts_streams = []
            for i, seg in enumerate(segments):
                if "tts_path" in seg and os.path.exists(seg["tts_path"]):
                    current_start = seg["start"]
                    tts_dur = self.get_duration(seg["tts_path"])
                    
                    # Check if it overlaps with the next segment
                    # Allow a small buffer of 0.1s
                    speed_factor = 1.0
                    if i < len(segments) - 1:
                        next_start = segments[i+1]["start"]
                        available_time = next_start - current_start - 0.1
                        if tts_dur > available_time and available_time > 0:
                            speed_factor = tts_dur / available_time
                    
                    # Cap speed factor at a reasonable range (0.5 to 4.0)
                    speed_factor = max(0.5, min(4.0, speed_factor))
                    
                    s = ffmpeg.input(seg["tts_path"])
                    
                    # Apply speedup if needed
                    if speed_factor > 1.05 or speed_factor < 0.95:
                        # Chain atempo for factors > 2.0 or < 0.5
                        if speed_factor > 2.0:
                            s = s.filter('atempo', 2.0).filter('atempo', speed_factor / 2.0)
                        elif speed_factor < 0.5:
                            s = s.filter('atempo', 0.5).filter('atempo', speed_factor / 0.5)
                        else:
                            s = s.filter('atempo', speed_factor)
                    
                    delay_ms = int(current_start * 1000)
                    s = s.filter('adelay', f'{delay_ms}|{delay_ms}')
                    tts_streams.append(s)

            if tts_streams:
                # 1. Mix all TTS segments into a single "new vocals" track
                num_tts = len(tts_streams)
                # amix scales by 1/n, so we boost it back
                vocals = ffmpeg.filter(tts_streams, 'amix', inputs=num_tts, duration='longest', dropout_transition=0)
                vocals = vocals.filter('volume', f'{num_tts}')
                
                # 2. Lower original background and boost new vocals
                bg_reduced = bg.filter('volume', '0.4')
                vocals_boosted = vocals.filter('volume', '1.3')
                
                # 3. Final mix (amix with 2 inputs scales by 0.5, so we multiply by 2)
                final_mixed = ffmpeg.filter([bg_reduced, vocals_boosted], 'amix', inputs=2, duration='longest', dropout_transition=0)
                final_mixed = final_mixed.filter('volume', '2.0')
            else:
                final_mixed = bg

            ffmpeg.output(final_mixed, output_path, acodec='pcm_s16le').run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"Error mixing audio: {e.stderr.decode() if e.stderr else str(e)}")
            return None
        except ffmpeg.Error as e:
            logger.error(f"Error mixing audio: {e.stderr.decode() if e.stderr else str(e)}")
            return None
