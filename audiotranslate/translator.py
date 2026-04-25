import argostranslate.package
import argostranslate.translate
import os
import logging

logger = logging.getLogger(__name__)

class Translator:
    def __init__(self, from_code="en", to_code="zh"):
        self.from_code = from_code
        self.to_code = to_code
        self._setup_packages()

    def _setup_packages(self):
        """Downloads and installs language packages if missing."""
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        
        # Filter for the desired pair
        package_to_install = next(
            filter(
                lambda x: x.from_code == self.from_code and x.to_code == self.to_code,
                available_packages
            ), None
        )
        
        if package_to_install:
            # Check if already installed
            installed_packages = argostranslate.package.get_installed_packages()
            is_installed = any(
                p.from_code == self.from_code and p.to_code == self.to_code 
                for p in installed_packages
            )
            
            if not is_installed:
                logger.info(f"Installing translation package: {self.from_code} -> {self.to_code}")
                argostranslate.package.install_from_path(package_to_install.download())
        else:
            # Fallback check if package exists but index update is slow
            logger.warning(f"Could not find translation package for {self.from_code} -> {self.to_code}")

    def translate(self, text):
        """Translates a single string."""
        if not text.strip():
            return ""
        return argostranslate.translate.translate(text, self.from_code, self.to_code)

    def translate_segments(self, segments):
        """Translates a list of transcription segments."""
        for segment in segments:
            segment["translated_text"] = self.translate(segment["text"])
        return segments
