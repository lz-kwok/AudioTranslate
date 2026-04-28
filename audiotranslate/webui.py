import os
import sys
import logging
import gradio as gr
import pandas as pd
import threading
from audiotranslate.processor import AudioProcessor
from audiotranslate.transcriber import Transcriber
from audiotranslate.generator import Generator
from audiotranslate.cloner import VoiceCloner
from audiotranslate.script_generator import ScriptGenerator

# Configure logging to capture for UI
class UIHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logs = []

    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append(log_entry)
        if len(self.logs) > 100:
            self.logs.pop(0)

ui_handler = UIHandler()
ui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(ui_handler)
logger = logging.getLogger(__name__)

class WebUI:
    def __init__(self):
        self.processor = None
        self.current_video = None
        self.segments = []
        self.workspace = ".translate_workspace"
        
    def get_logs(self):
        return "\n".join(ui_handler.logs)

    def run_analyze(self, video_path, model_size, source_lang):
        if not video_path:
            return None, "Please upload a video first."
        
        try:
            self.current_video = video_path
            self.processor = AudioProcessor(video_path, self.workspace)
            
            logger.info("--- Stage 1: Extracting Audio ---")
            audio_path = self.processor.extract_audio()
            
            logger.info("--- Stage 2: Separating Vocals ---")
            vocals_path, _ = self.processor.separate_vocals(audio_path)
            
            logger.info("--- Stage 3: Analyzing Dialogue ---")
            transcriber = Transcriber(model_size=model_size)
            self.segments = transcriber.transcribe(vocals_path, language=source_lang, diarize=True)
            
            # Convert segments to DataFrame for Gradio Dataframe component
            data = []
            for seg in self.segments:
                data.append({
                    "Speaker": seg.get("speaker", "speaker_0"),
                    "Start": seg["start"],
                    "End": seg["end"],
                    "Original Text": seg.get("text", ""),
                    "New Text": ""
                })
            
            return pd.DataFrame(data), "Analysis complete. Please edit the 'New Text' column."
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return None, f"Error: {e}"

    def run_synthesize(self, video_path, script_df, target_lang, voice, clone, diarize, emotion, short_drama):
        if not video_path or script_df is None:
            return None, "Please analyze the video and provide a script first."
        
        try:
            # Reconstruct segments from DataFrame
            final_segments = []
            for _, row in script_df.iterrows():
                # Only include segments that have new text or we keep original?
                # For short drama synthesis, we usually want new text.
                text = row["New Text"] if row["New Text"] else row["Original Text"]
                final_segments.append({
                    "start": row["Start"],
                    "end": row["End"],
                    "speaker": row["Speaker"],
                    "text": text,
                    "translated_text": text
                })
            
            self.processor = AudioProcessor(video_path, self.workspace)
            audio_path = self.processor.extract_audio()
            vocals_path, bg_path = self.processor.separate_vocals(audio_path)
            
            logger.info("--- Stage 4: Generating TTS ---")
            generator = Generator()
            cloner = None
            if clone:
                cloner = VoiceCloner()
            
            # Use original segments for diarization reference if cloning
            original_segments = None
            if clone:
                transcriber = Transcriber()
                original_segments = transcriber.transcribe(vocals_path, diarize=True)

            for i, seg in enumerate(final_segments):
                output_tts = os.path.join(self.workspace, f"tts_{i}.mp3")
                
                # Setup cloning if enabled
                ref_audio = None
                if clone and cloner:
                    speaker_id = seg.get("speaker", "speaker_0")
                    ref_audio = cloner.extract_reference(vocals_path, original_segments, speaker_id)
                
                # Generate
                success = generator.generate_ssml(
                    seg["text"], 
                    output_tts, 
                    voice=voice,
                    ref_audio=ref_audio,
                    emotion=emotion if clone else False
                )
                if success:
                    seg["tts_path"] = output_tts
            
            logger.info("--- Stage 5: Mixing Audio ---")
            output_audio = os.path.join(self.workspace, "final_mixed.wav")
            self.processor.mix_translated_audio(bg_path, final_segments, output_audio)
            
            logger.info("--- Stage 6: Final Merging ---")
            output_video = f"{os.path.splitext(video_path)[0]}_{target_lang}_webui.mp4"
            
            # Subtitle handling
            srt_path = None
            if short_drama:
                srt_path = os.path.join(self.workspace, "subtitles.srt")
                self.processor.generate_srt(final_segments, srt_path)
            
            result = self.processor.merge_audio_video(video_path, output_audio, output_video, srt_path=srt_path)
            
            if result:
                logger.info(f"Success! Output saved to: {result}")
                return result, "Synthesis complete!"
            else:
                return None, "Merging failed."
                
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return None, f"Error: {e}"

    def run_generate_ai_script(self, theme, script_df, api_key):
        if not theme:
            return script_df, "Please enter a theme."
        if script_df is None or len(script_df) == 0:
            return script_df, "Please analyze a video first."
        
        try:
            logger.info(f"--- Generating AI Script for theme: {theme} ---")
            generator = ScriptGenerator(api_key=api_key)
            # Pass original segments as context
            ai_segments = generator.generate_from_theme(theme, original_segments=self.segments)
            
            # Update DataFrame
            new_df = script_df.copy()
            for i, seg in enumerate(ai_segments):
                if i < len(new_df):
                    new_df.at[i, "New Text"] = seg["text"]
            
            return new_df, "AI Script generated. You can further edit it manually."
        except Exception as e:
            logger.error(f"AI Script generation failed: {e}")
            return script_df, f"Error: {e}"

    def run_generate_promo(self, script_df, api_key):
        if script_df is None or len(script_df) == 0:
            return "Please provide a script first."
        
        try:
            # Gather text from script
            script_text = ""
            for _, row in script_df.iterrows():
                text = row["New Text"] if row["New Text"] else row["Original Text"]
                script_text += f"{row['Speaker']}: {text}\n"
            
            logger.info("--- Generating Social Media Promo Copy ---")
            generator = ScriptGenerator(api_key=api_key)
            promo = generator.generate_promo_copy(script_text)
            return promo
        except Exception as e:
            logger.error(f"Promo generation failed: {e}")
            return f"Error: {e}"

    def launch(self):
        with gr.Blocks(title="AudioTranslate WebUI", theme=gr.themes.Soft()) as demo:
            gr.Markdown("# 🎬 AudioTranslate: AI Short Drama Engine")
            gr.Markdown("Transform any video into a multi-speaker AI short drama with voice cloning and vertical layout.")
            
            with gr.Tab("1. Configuration & Analyze"):
                with gr.Row():
                    with gr.Column():
                        video_input = gr.Video(label="Input Video")
                        with gr.Row():
                            source_lang = gr.Dropdown(choices=["en", "zh", "ja", "fr", "de"], value="en", label="Source Language")
                            target_lang = gr.Dropdown(choices=["zh", "en", "ja"], value="zh", label="Target Language")
                        model_size = gr.Dropdown(choices=["tiny", "base", "small", "medium", "large-v3"], value="base", label="Whisper Model Size")
                        analyze_btn = gr.Button("🔍 1. Analyze Video Dialogue", variant="primary")
                    
                    with gr.Column():
                        gr.Markdown("### 🤖 AI Scripting")
                        theme_input = gr.Textbox(label="Video Theme / Topic", placeholder="e.g. AI提效：个人提效不等于组织提效")
                        ai_script_btn = gr.Button("🪄 2. Generate AI Script", variant="secondary")
                        
                        gr.Markdown("### ⚙️ Processing Options")
                        api_key = gr.Textbox(label="OpenAI API Key (Optional)", type="password", placeholder="sk-...")
                        clone = gr.Checkbox(label="Enable Voice Cloning", value=True)
                        diarize = gr.Checkbox(label="Speaker Diarization", value=True)
                        emotion = gr.Checkbox(label="Emotion-Aware (Experimental)", value=False)
                        short_drama = gr.Checkbox(label="Short Drama Layout (9:16)", value=True)
                        voice = gr.Textbox(label="Fallback TTS Voice", placeholder="e.g. zh-CN-YunxiNeural")
                        
                script_output = gr.DataFrame(
                    label="Dialogue Script (Edit 'New Text')",
                    headers=["Speaker", "Start", "End", "Original Text", "New Text"],
                    datatype=["str", "number", "number", "str", "str"],
                    interactive=True
                )
                status_box = gr.Textbox(label="Status", interactive=False)

            with gr.Tab("2. Synthesis & Output"):
                with gr.Row():
                    with gr.Column():
                        synthesize_btn = gr.Button("🚀 3. Synthesize Final Video", variant="primary")
                        video_output = gr.Video(label="Result Video")
                    
                    with gr.Column():
                        refresh_btn = gr.Button("🔄 Refresh Logs")
                        log_output = gr.Textbox(label="Process Logs", lines=15, interactive=False)

            with gr.Tab("3. Social Media Promo"):
                promo_btn = gr.Button("📱 Generate Promo Copy (Video Channel / TikTok)", variant="primary")
                promo_output = gr.Textbox(label="Promo Copy", lines=10, interactive=True)
            
            # Event Bindings
            analyze_btn.click(
                self.run_analyze,
                inputs=[video_input, model_size, source_lang],
                outputs=[script_output, status_box]
            )

            ai_script_btn.click(
                self.run_generate_ai_script,
                inputs=[theme_input, script_output, api_key],
                outputs=[script_output, status_box]
            )
            
            synthesize_btn.click(
                self.run_synthesize,
                inputs=[video_input, script_output, target_lang, voice, clone, diarize, emotion, short_drama],
                outputs=[video_output, status_box]
            )

            promo_btn.click(
                self.run_generate_promo,
                inputs=[script_output, api_key],
                outputs=[promo_output]
            )
            
            refresh_btn.click(self.get_logs, None, log_output)
            
            # Update logs when loading
            demo.load(self.get_logs, None, log_output)

        demo.launch(server_port=7861)

if __name__ == "__main__":
    ui = WebUI()
    ui.launch()
