"""Gemini AI Text-to-Speech engine."""

import os
import time
import random
from typing import List

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from ..engine import TTSEngine


class GeminiEngine(TTSEngine):
    """Gemini AI Text-to-Speech engine using Google Generative AI SDK."""

    # Gemini 2.0 supported voices (available in Multimodal Live/Speech)
    SUPPORTED_VOICES = [
        "Aoede", "Charon", "Fenrir", "Kore", "Puck"
    ]

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def get_name(self) -> str:
        """Get engine name."""
        return "Gemini AI (Cloud)"

    def get_supported_voices(self) -> List[str]:
        """Get supported voice names."""
        return self.SUPPORTED_VOICES.copy()

    def get_voice_info(self) -> str:
        """Get voice information."""
        return f"Gemini voices: {', '.join(self.SUPPORTED_VOICES)}"

    def get_chunk_size(self) -> int:
        """Return recommended chunk size for this engine."""
        return 4096

    def synthesize(self, text: str, voice: str) -> bytes:
        """
        Synthesize speech using Gemini.

        Args:
            text: Text to speak
            voice: Voice name (e.g., "Aoede", "Charon")

        Returns:
            MP3 audio bytes
        """
        if not GEMINI_AVAILABLE:
            raise RuntimeError(
                "google-generativeai package not installed. "
                "Please run: pip install -U google-generativeai"
            )

        if not self.api_key:
            # Re-check in case it was set after init
            self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not self.api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set. "
                    "Please set it to use the Gemini engine."
                )
            genai.configure(api_key=self.api_key)

        if voice not in self.SUPPORTED_VOICES:
            voice = "Aoede"

        max_retries = 5
        base_delay = 5  # Start with 5 seconds

        # Force use of experimental model since we know it exists (gave 429, not 404)
        model_name = "gemini-2.0-flash-exp"
        
        # Add a delay BEFORE the request to enforce rate limits
        # Free tier limit is often ~2-3 RPM for experimental models
        # We'll wait 20 seconds between chunks to be safe
        print(f"Debug: Waiting 20s to respect rate limits for {model_name}...")
        time.sleep(20)

        for attempt in range(max_retries):
            try:
                print(f"Debug: Trying model {model_name} (Attempt {attempt+1})")
                
                model = genai.GenerativeModel(model_name)
                
                # Construct the prompt
                prompt = f"Please read this text aloud exactly as written: {text}"
                
                # Configure the generation for audio output
                # Added request_options with timeout to prevent freezing
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "speech_config": {
                            "voice_config": {
                                "prebuilt_voice_config": {
                                    "voice_name": voice
                                }
                            }
                        }
                    },
                    request_options={"timeout": 60} # Increased timeout to 60s
                )
                
                # Extract audio data from response
                # Debug: print available parts
                if not response.candidates:
                    print(f"Debug: No candidates returned. Feedback: {response.prompt_feedback}")
                
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        # print(f"Debug: Found part with mime_type: {part.inline_data.mime_type if part.inline_data else 'None'}")
                        if hasattr(part, 'inline_data') and part.inline_data:
                            if part.inline_data.mime_type in ["audio/mpeg", "audio/mp3", "audio/wav"]:
                                return part.inline_data.data
                
                # Fallback for different response structures
                if hasattr(response, 'audio_data') and response.audio_data:
                    return response.audio_data
                
                # If we get here, print what we actually got to help debugging
                print("Debug: Response content:")
                try:
                    print(response.text)
                except:
                    print("No text in response")
                print(f"Debug: Full response keys: {dir(response)}")

                raise RuntimeError("Gemini did not return any audio data.")

            except Exception as e:
                # Check for 429 (Resource Exhausted) or 503 (Service Unavailable)
                error_str = str(e)
                if "429" in error_str or "Resource has been exhausted" in error_str:
                    if attempt < max_retries - 1:
                        sleep_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        print(f"Gemini quota exceeded. Retrying in {sleep_time:.2f}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(sleep_time)
                        continue
                
                # Re-raise other errors or if retries exhausted
                if "404" in error_str or "not found" in error_str.lower():
                    raise RuntimeError(
                        f"Gemini model 'gemini-2.0-flash' not found. "
                        f"Error: {e}"
                    )
                raise RuntimeError(f"Gemini synthesis failed: {e}")