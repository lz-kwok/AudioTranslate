import os
import torch
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class VoiceCloner:
    def __init__(self, checkpoint_dir: str = "checkpoints_v2", device: str = "cpu"):
        self.device = device
        self.checkpoint_dir = checkpoint_dir
        self.converter = None
        self.se_extractor = None
        self.is_available = False
        
        # We'll try to import OpenVoice. If it's not installed, we'll gracefully handle it.
        try:
            from openvoice import se_extractor as extractor
            from openvoice.api import ToneColorConverter
            
            self.se_extractor = extractor
            
            config_path = os.path.join(checkpoint_dir, "converter", "config.json")
            ckpt_path = os.path.join(checkpoint_dir, "converter", "checkpoint.pth")
            
            if os.path.exists(config_path) and os.path.exists(ckpt_path):
                self.converter = ToneColorConverter(config_path, device=self.device, enable_watermark=False)
                self.converter.load_ckpt(ckpt_path)
                self.is_available = True
                logger.info("OpenVoice V2 Cloner initialized successfully.")
            else:
                logger.warning(f"OpenVoice checkpoints not found at {checkpoint_dir}. Cloning will be disabled.")
                logger.warning("Please download checkpoints from https://github.com/myshell-ai/OpenVoice and place them in the checkpoints_v2 directory.")
        except ImportError as e:
            logger.warning(f"OpenVoice library not found: {e}. Cloning will be disabled.")
            logger.warning("To use cloning, please install OpenVoice: pip install openvoice")
            # Try to add path manually
            import sys
            ov_path = os.path.join(os.getcwd(), "OpenVoice")
            if os.path.exists(ov_path) and ov_path not in sys.path:
                sys.path.append(ov_path)
                try:
                    from openvoice import se_extractor as extractor
                    from openvoice.api import ToneColorConverter
                    self.se_extractor = extractor
                    # Re-run initialization
                    config_path = os.path.join(checkpoint_dir, "converter", "config.json")
                    ckpt_path = os.path.join(checkpoint_dir, "converter", "checkpoint.pth")
                    if os.path.exists(config_path) and os.path.exists(ckpt_path):
                        self.converter = ToneColorConverter(config_path, device=self.device, enable_watermark=False)
                        self.converter.load_ckpt(ckpt_path)
                        self.is_available = True
                        logger.info("OpenVoice V2 Cloner initialized successfully after path fix.")
                except Exception as e2:
                    logger.warning(f"Manual path fix failed: {e2}")

    def extract_se(self, audio_path: str, output_dir: str = ".processed", vad: bool = True):
        """Extracts Speaker Embedding (SE) from reference audio."""
        if not self.is_available or self.converter is None:
            return None
        
        try:
            if not vad:
                # Direct extraction without VAD or splitting, good for short/clean generated audio
                return self.converter.extract_se(audio_path)
            
            os.makedirs(output_dir, exist_ok=True)
            target_se, _ = self.se_extractor.get_se(
                audio_path, 
                self.converter, 
                target_dir=output_dir, 
                vad=True
            )
            return target_se
        except Exception as e:
            logger.error(f"Failed to extract SE from {audio_path}: {e}")
            return None

    def convert(self, src_path: str, src_se: torch.Tensor, tgt_se: torch.Tensor, output_path: str):
        """Converts the tone color of src_path to match tgt_se."""
        if not self.is_available:
            return src_path
        
        try:
            self.converter.convert(
                audio_src_path=src_path,
                src_se=src_se,
                tgt_se=tgt_se,
                output_path=output_path,
                message="@AudioTranslate"
            )
            return output_path
        except Exception as e:
            logger.error(f"Tone color conversion failed: {e}")
            return src_path

    def get_audio_se(self, audio_path: str, output_dir: str = ".processed"):
        """Utility to get SE for a single audio file, typically generated TTS."""
        return self.extract_se(audio_path, output_dir, vad=False)
