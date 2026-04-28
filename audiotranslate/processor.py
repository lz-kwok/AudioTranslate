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

    def generate_srt(self, segments, srt_path):
        """Generates an SRT file from segments."""
        try:
            with open(srt_path, "w", encoding="utf-8") as f:
                for i, seg in enumerate(segments):
                    start = self._format_timestamp(seg["start"])
                    end = self._format_timestamp(seg["end"])
                    text = seg.get("translated_text", seg.get("text", ""))
                    
                    f.write(f"{i + 1}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")
            return srt_path
        except Exception as e:
            logger.error(f"Error generating SRT: {e}")
            return None

    def save_analysis(self, segments, output_path):
        """Saves video dialogue segments to a Markdown file for manual scripting."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# Video Analysis: {os.path.basename(self.input_path)}\n\n")
                f.write("Use the table below to write your new script. Do not modify the 'Start', 'End', or 'Speaker' columns to maintain timing.\n\n")
                f.write("| Speaker | Start | End | Duration | Original Text | New Text (Action) |\n")
                f.write("|---------|-------|-----|----------|---------------|-------------------|\n")
                
                for seg in segments:
                    spk = seg.get("speaker", "speaker_0")
                    start = f"{seg['start']:.2f}s"
                    end = f"{seg['end']:.2f}s"
                    dur = f"{seg['end'] - seg['start']:.2f}s"
                    text = seg.get("text", "").replace("\n", " ")
                    f.write(f"| {spk} | {start} | {end} | {dur} | {text} | | \n")
            
            logger.info(f"Analysis saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            return None

    def _format_timestamp(self, seconds):
        """Formats seconds into SRT timestamp (HH:MM:SS,mmm)."""
        td = float(seconds)
        h = int(td // 3600)
        m = int((td % 3600) // 60)
        s = int(td % 60)
        ms = int((td % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def merge_audio_video(self, video_path, audio_path, output_path, srt_path=None, short_drama=False):
        """
        Merges new audio with original video, optionally adding subtitles and 
        applying short drama (vertical) layout.
        """
        try:
            video = ffmpeg.input(video_path)
            audio = ffmpeg.input(audio_path)
            
            v_stream = video.video
            
            if short_drama:
                # Short drama layout: 9:16 vertical video
                # 1. Scale background to fill 1080x1920 and blur it
                bg = (
                    video.video
                    .filter('scale', 1080, 1920, force_original_aspect_ratio='increase')
                    .filter('crop', 1080, 1920)
                    .filter('boxblur', 20, 10)
                )
                
                # 2. Scale original video to fit width 1080
                fg = video.video.filter('scale', 1080, -1)
                                # 3. Overlay original video on blurred background
                v_stream = bg.overlay(fg, x=0, y='(H-h)/2')
            
            if srt_path:
                # Burn subtitles into video
                # On Windows, absolute paths with colons (C:/...) often fail in the subtitles filter.
                # Using a relative path is much more reliable.
                try:
                    rel_srt = os.path.relpath(srt_path).replace("\\", "/")
                except ValueError:
                    # Fallback to absolute if on different drives, but try to escape properly
                    rel_srt = os.path.abspath(srt_path).replace("\\", "/").replace(":", "\\:")
                
                # Font settings for subtitles (Force high visibility)
                v_stream = v_stream.filter('subtitles', rel_srt, force_style='FontSize=16,Alignment=6,OutlineColour=&H40000000,BorderStyle=3,Outline=1,Shadow=0')

            # Run output
            (
                ffmpeg.output(v_stream, audio.audio, output_path, 
                              vcodec='libx264', acodec='aac', 
                              shortest=None, pix_fmt='yuv420p')
                .run(overwrite_output=True)
            )
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"Error merging files: {e.stderr.decode() if e.stderr else str(e)}")
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
