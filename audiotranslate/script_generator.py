import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

class ScriptGenerator:
    def __init__(self, api_key=None, api_base="https://api.openai.com/v1"):
        """
        Initializes the script generator.
        Uses OpenAI-compatible API.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_base = api_base or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

    def generate_from_theme(self, theme, duration_limit=60, num_speakers=2):
        """
        Generates a dialogue script based on a theme.
        Returns a list of segments.
        """
        if not self.api_key:
            logger.warning("No API key found for ScriptGenerator. Returning a sample script.")
            return self._get_sample_script(theme)

        prompt = f"""
        Act as a professional short drama scriptwriter. 
        Create a compelling dialogue script for a short video (approx {duration_limit} seconds).
        Theme: {theme}
        Number of Speakers: {num_speakers}
        
        Format the output as a JSON list of objects:
        [
          {{"speaker": "speaker_0", "text": "...", "duration": 5.0}},
          {{"speaker": "speaker_1", "text": "...", "duration": 4.5}}
        ]
        
        Ensure the 'text' is in Chinese (default for short dramas). 
        'duration' should be an estimate of how long the line takes to speak in seconds.
        Only return the JSON.
        """

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-3.5-turbo", # Or gpt-4
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            
            response = requests.post(f"{self.api_base}/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            
            content = response.json()['choices'][0]['message']['content']
            # Basic JSON extraction in case there's markdown wrap
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            script = json.loads(content)
            
            # Convert to internal segment format
            segments = []
            current_time = 0.5
            for i, item in enumerate(script):
                dur = item.get("duration", 3.0)
                segments.append({
                    "start": current_time,
                    "end": current_time + dur,
                    "speaker": item.get("speaker", f"speaker_{i % num_speakers}"),
                    "text": item.get("text", ""),
                    "translated_text": item.get("text", "") # Already in target language
                })
                current_time += dur + 0.5 # Add small pause
                
            return segments

        except Exception as e:
            logger.error(f"Failed to generate script via LLM: {e}")
            return self._get_sample_script(theme)

    def load_from_markdown(self, file_path):
        """
        Parses a manual script from a Markdown file.
        Expected format: | Speaker | Start | End | Duration | Original Text | New Text |
        """
        try:
            segments = []
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            for line in lines:
                if line.startswith("|") and "Speaker" not in line and "---" not in line:
                    parts = [p.strip() for p in line.split("|")]
                    # | empty | speaker | start | end | dur | original | new | empty |
                    if len(parts) >= 7:
                        spk = parts[1]
                        start = float(parts[2].replace("s", ""))
                        end = float(parts[3].replace("s", ""))
                        # New text is in parts[6]
                        new_text = parts[6]
                        
                        if new_text:
                            segments.append({
                                "start": start,
                                "end": end,
                                "speaker": spk,
                                "text": new_text,
                                "translated_text": new_text
                            })
            
            logger.info(f"Loaded {len(segments)} segments from {file_path}")
            return segments
        except Exception as e:
            logger.error(f"Error loading script from markdown: {e}")
            return []

    def _get_sample_script(self, theme):
        """Returns a generic sample script if LLM fails."""
        return [
            {
                "start": 0.5,
                "end": 4.5,
                "speaker": "speaker_0",
                "text": f"你听说了吗？关于{theme}的事情。",
                "translated_text": f"你听说了吗？关于{theme}的事情。"
            },
            {
                "start": 5.0,
                "end": 9.0,
                "speaker": "speaker_1",
                "text": "当然，这在圈子里已经传开了，真是不可思议。",
                "translated_text": "当然，这在圈子里已经传开了，真是不可思议。"
            }
        ]
