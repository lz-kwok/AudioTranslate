import click
import sys
import os
import logging
from tqdm import tqdm
from audiotranslate.processor import AudioProcessor
from audiotranslate.transcriber import Transcriber
from audiotranslate.translator import Translator
from audiotranslate.generator import Generator
from audiotranslate.cloner import VoiceCloner
from audiotranslate.script_generator import ScriptGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@click.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--target_lang', '-t', default='zh', help='Target language for translation (default: zh)')
@click.option('--source_lang', '-s', default='en', help='Source language of the audio (default: en)')
@click.option('--output', '-o', help='Path to output file')
@click.option('--device', '-d', default='cpu', type=click.Choice(['cuda', 'cpu']), help='Device to use for processing')
@click.option('--model_size', default='base', help='Whisper model size (tiny, base, small, medium, large-v3)')
@click.option('--voice', help='Specific TTS voice (e.g., zh-CN-YunxiNeural)')
@click.option('--clone', is_flag=True, help='Clone original voice timbre (requires OpenVoice)')
@click.option('--diarize', is_flag=True, help='Enable multi-speaker detection and cloning')
@click.option('--emotion', is_flag=True, help='Enable emotion-aware TTS prosody (requires --clone)')
@click.option('--subtitle', is_flag=True, help='Generate and burn subtitles into the video')
@click.option('--short_drama', is_flag=True, help='Convert video to vertical (9:16) "short drama" layout with subtitles')
@click.option('--theme', help='Automatically generate a new dialogue script based on this theme (Redubs the video)')
@click.option('--analyze', is_flag=True, help='Extract video dialogue info to Markdown for manual scripting.')
@click.option('--script', type=click.Path(exists=True), help='Path to a manual script file (Markdown) to synthesize.')
def main(input_path, target_lang, source_lang, output, device, model_size, voice, clone, diarize, emotion, subtitle, short_drama, theme, analyze, script):
    """AudioTranslate: Local video/audio translation with background preservation."""
    if not output:
        base, ext = os.path.splitext(input_path)
        output = f"{base}_{target_lang}{ext}"

    click.echo(f"Processing: {input_path}")
    
    workspace = ".translate_workspace"
    processor = AudioProcessor(input_path, workspace)
    
    # Stage 1: Extraction
    click.echo("--- Stage 1: Extracting Audio ---")
    audio_path = processor.extract_audio()
    if not audio_path:
        click.echo("Error: Failed to extract audio.")
        return
    
    # Stage 2: Vocal Separation
    click.echo("--- Stage 2: Separating Vocals (Demucs) ---")
    vocals_path, bg_path = processor.separate_vocals(audio_path)
    if not vocals_path or not bg_path:
        click.echo("Error: Vocal separation failed.")
        return
    
    # Stage 3-4: Transcription / Script Loading / Analysis
    original_segments = None
    final_segments = None
    
    if script:
        click.echo(f"--- Stage 3: Loading Manual Script: {script} ---")
        script_loader = ScriptGenerator()
        final_segments = script_loader.load_from_markdown(script)
        
        # We still need original speaker diarization for cloning references
        if clone:
            click.echo("--- Stage 3b: Diarizing original video for voice references ---")
            transcriber = Transcriber(model_size=model_size, device=device)
            original_segments = transcriber.transcribe(vocals_path, language=source_lang, diarize=True)
            
    elif analyze:
        click.echo("--- Stage 3: Analyzing Video for Manual Scripting ---")
        transcriber = Transcriber(model_size=model_size, device=device)
        segments = transcriber.transcribe(vocals_path, language=source_lang, diarize=True)
        
        analysis_path = f"{os.path.splitext(input_path)[0]}_analysis.md"
        processor.save_analysis(segments, analysis_path)
        click.echo(f"Success! Analysis saved to: {analysis_path}")
        click.echo("Please edit the 'New Text' column in the Markdown file and run again with --script.")
        return
        
    elif theme:
        click.echo(f"--- Stage 3: Generating Script from Theme: {theme} ---")
        generator_llm = ScriptGenerator()
        final_segments = generator_llm.generate_from_theme(theme)
        
        if clone:
            click.echo("--- Stage 3b: Diarizing original video for voice references ---")
            transcriber = Transcriber(model_size=model_size, device=device)
            original_segments = transcriber.transcribe(vocals_path, language=source_lang, diarize=True)
    else:
        # Standard Translation Pipeline
        click.echo(f"--- Stage 3: Transcribing ({source_lang}) {'with Diarization' if diarize else ''} ---")
        transcriber = Transcriber(model_size=model_size, device=device)
        segments = transcriber.transcribe(vocals_path, language=source_lang, diarize=diarize)
        original_segments = segments
        
        click.echo(f"--- Stage 4: Translating ({source_lang} -> {target_lang}) ---")
        translator = Translator(from_code=source_lang, to_code=target_lang)
        final_segments = translator.translate_segments(segments)
    
    # Stage 5: TTS Generation
    click.echo("--- Stage 5: Generating TTS ---")
    if not final_segments:
        click.echo("Error: No segments to process.")
        return
        
    if not voice:
        voice_map = {"zh": "zh-CN-XiaoxiaoNeural", "en": "en-US-GuyNeural"}
        voice = voice_map.get(target_lang, "zh-CN-XiaoxiaoNeural")
    
    cloner = None
    if clone:
        cloner = VoiceCloner(device=device)
    
    generator = Generator(voice=voice, cloner=cloner)
    final_segments = generator.generate_segments(
        final_segments, 
        os.path.join(workspace, "tts"),
        reference_audio=vocals_path if clone else None,
        use_emotion=emotion,
        reference_segments=original_segments
    )
    
    # Stage 6: Mixing Audio
    click.echo("--- Stage 6: Mixing Audio ---")
    mixed_audio = os.path.join(workspace, "final_audio.wav")
    processor.mix_translated_audio(bg_path, final_segments, mixed_audio)
    
    # Stage 7: Subtitles (Optional)
    srt_path = None
    if subtitle or short_drama:
        click.echo("--- Stage 7: Generating Subtitles ---")
        srt_path = os.path.join(workspace, "subtitles.srt")
        processor.generate_srt(final_segments, srt_path)
    
    # Stage 8: Final Merge
    click.echo(f"--- Stage 8: Merging with Video {'(Short Drama Mode)' if short_drama else ''} ---")
    # Determine if input is audio or video
    is_video = any(input_path.lower().endswith(ext) for ext in ['.mp4', '.avi', '.mkv', '.mov'])
    
    if is_video:
        processor.merge_audio_video(input_path, mixed_audio, output, srt_path=srt_path, short_drama=short_drama)
    else:
        # If input is audio, just copy the mixed result
        import shutil
        shutil.copy2(mixed_audio, output)
    
    click.echo(f"Success! Output saved to: {output}")

if __name__ == '__main__':
    main()
