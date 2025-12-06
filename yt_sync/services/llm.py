import json
import logging
from django.conf import settings
from litellm import completion

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = "claude-3-haiku-20240307"

    def generate_summary(self, transcript_text):
        """
        Generates a structured summary from the transcript using LLM.
        """
        if not transcript_text:
            return None

        prompt = f"""
You are an expert content analyst. Your task is to analyze the following video transcript and extract structured information.

Transcript:
{transcript_text[:25000]}  # Truncate to avoid context limit issues if very long, though Haiku has 200k context.

Please return a valid JSON object with the following structure:
{{
  "summary": "Concise TL;DR of the video (max 3 sentences)",
  "tags": ["tag1", "tag2", "tag3"],
  "categories": ["Category1", "Category2"],
  "main_ideas": ["Idea 1", "Idea 2", "Idea 3"],
  "key_moments": [
    {{"timestamp": "HH:MM:SS", "description": "Brief description"}}
  ]
}}

Ensure the JSON is valid and strictly follows this schema. Do not include any other text before or after the JSON.
"""

        try:
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                api_key=self.api_key
            )
            
            content = response.choices[0].message.content
            
            # clean up potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            return json.loads(content)

        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return None
