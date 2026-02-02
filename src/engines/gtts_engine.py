"""Google Text-to-Speech engine."""

import io
from typing import List

from gtts import gTTS

from ..engine import TTSEngine


class gTTSEngine(TTSEngine):
    """Google Text-to-Speech engine using gTTS library."""

    # Supported languages (ISO 639-1 codes)
    SUPPORTED_VOICES = [
        "en", "es", "fr", "de", "it", "pt", "pt-br", "ru", "ja", "zh-cn",
        "zh-tw", "ko", "ar", "hi", "th", "pl", "tr", "nl", "sv", "da",
        "no", "fi", "hu", "cs", "ro", "el", "he", "vi", "id", "fa",
    ]

    def get_name(self) -> str:
        """Get engine name."""
        return "Google TTS (gTTS)"

    def get_supported_voices(self) -> List[str]:
        """Get supported languages."""
        return self.SUPPORTED_VOICES.copy()

    def get_voice_info(self) -> str:
        """Get voice information."""
        return "Language codes: en, es, fr, de, it, pt, pt-br, ru, ja, zh-cn, etc."

    def get_chunk_size(self) -> int:
        """Return recommended chunk size for this engine."""
        return 4096

    def synthesize(self, text: str, voice: str, slow: bool = False) -> bytes:
        """
        Synthesize speech using Google TTS.

        Args:
            text: Text to speak
            voice: Language code (e.g., "en", "es", "fr")
            slow: If True, speak slower

        Returns:
            MP3 audio bytes
        """
        if voice not in self.SUPPORTED_VOICES:
            raise ValueError(
                f"Unsupported language: {voice}. "
                f"Supported: {', '.join(self.SUPPORTED_VOICES)}"
            )

        try:
            tts = gTTS(text=text, lang=voice, slow=slow)
            mp3_buffer = io.BytesIO()
            tts.write_to_fp(mp3_buffer)
            mp3_buffer.seek(0)
            return mp3_buffer.getvalue()
        except Exception as e:
            raise RuntimeError(f"gTTS synthesis failed: {e}")
