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
def main(input_path, target_lang, source_lang, output, device, model_size, voice, clone):
    """AudioTranslate: Local video/audio translation with background preservation."""
    if not output:
        base, ext = os.path.splitext(input_path)
        output = f"{base}_{target_lang}{ext}"

    click.echo(f"Processing: {input_path}")
    click.echo(f"Source Language: {source_lang}")
    click.echo(f"Target Language: {target_lang}")
    
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
    
    # Stage 3: Transcription
    click.echo(f"--- Stage 3: Transcribing ({source_lang}) ---")
    transcriber = Transcriber(model_size=model_size, device=device)
    segments = transcriber.transcribe(vocals_path, language=source_lang)
    
    # Stage 4: Translation
    click.echo(f"--- Stage 4: Translating ({source_lang} -> {target_lang}) ---")
    translator = Translator(from_code=source_lang, to_code=target_lang)
    translated_segments = translator.translate_segments(segments)
    
    # Stage 5: TTS Generation
    click.echo("--- Stage 5: Generating TTS ---")
    if not voice:
        # For now default to a reasonable voice for target_lang
        voice_map = {
            "zh": "zh-CN-XiaoxiaoNeural",
            "en": "en-US-GuyNeural"
        }
        voice = voice_map.get(target_lang, "zh-CN-XiaoxiaoNeural")
    cloner = None
    if clone:
        cloner = VoiceCloner(device=device)
    
    generator = Generator(voice=voice, cloner=cloner)
    final_segments = generator.generate_segments(
        translated_segments, 
        os.path.join(workspace, "tts"),
        reference_audio=vocals_path if clone else None
    )
    
    # Stage 6: Mixing
    click.echo("--- Stage 6: Mixing Audio ---")
    mixed_audio = os.path.join(workspace, "final_audio.wav")
    processor.mix_translated_audio(bg_path, final_segments, mixed_audio)
    
    # Stage 7: Final Merge
    click.echo("--- Stage 7: Merging with Video ---")
    # Determine if input is audio or video
    is_video = any(input_path.lower().endswith(ext) for ext in ['.mp4', '.avi', '.mkv', '.mov'])
    
    if is_video:
        processor.merge_audio_video(input_path, mixed_audio, output)
    else:
        # If input is audio, just copy the mixed result
        import shutil
        shutil.copy2(mixed_audio, output)
    
    click.echo(f"Success! Output saved to: {output}")

if __name__ == '__main__':
    main()
