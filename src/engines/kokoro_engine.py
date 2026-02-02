"""Kokoro TTS engine."""

import io
from typing import List

from ..engine import TTSEngine


class KokoroEngine(TTSEngine):
    """Kokoro TTS engine (runs locally, high-quality voices)."""

    # Supported voices - curated set across languages
    # Format: {lang_code}_{speaker}_{name} or {lang_code}_{name}
    # a = American English, b = British English, j = Japanese, etc.
    SUPPORTED_VOICES = [
        # American English
        "af_heart", "af_bella", "af_nicole", "af_sarah", "af_sky",
        "am_adam", "am_michael",
        # British English
        "bf_emma", "bf_isabella",
        "bm_george", "bm_lewis",
    ]

    # Pipeline instance (lazy loaded)
    _pipeline = None

    def get_name(self) -> str:
        """Get engine name."""
        return "Kokoro TTS (Local)"

    def get_supported_voices(self) -> List[str]:
        """Get supported voice names."""
        return self.SUPPORTED_VOICES.copy()

    def get_voice_info(self) -> str:
        """Get voice information."""
        return "Voices: af_heart, af_bella, am_adam, bf_emma, bm_george, etc."

    def get_chunk_size(self) -> int:
        """Return recommended chunk size for this engine."""
        return 2000

    def _ensure_pipeline_loaded(self):
        """Lazy load the Kokoro pipeline."""
        if KokoroEngine._pipeline is not None:
            return

        print("Debug: Initializing Kokoro engine...")

        try:
            from kokoro import KPipeline
        except ImportError:
            raise RuntimeError(
                "kokoro package not installed. "
                "Please run: pip install kokoro soundfile"
            )

        # Initialize with American English by default
        # The pipeline will handle voice-specific language codes
        print("Debug: Loading Kokoro pipeline (this may take a while on first run)...")
        KokoroEngine._pipeline = KPipeline(lang_code="a")
        print("Debug: Kokoro pipeline loaded.")

    def synthesize(self, text: str, voice: str) -> bytes:
        """
        Synthesize speech using Kokoro TTS.

        Args:
            text: Text to speak
            voice: Voice name (e.g., "af_heart", "am_adam")

        Returns:
            WAV audio bytes
        """
        if voice not in self.SUPPORTED_VOICES:
            raise ValueError(
                f"Unsupported voice: {voice}. "
                f"Supported: {', '.join(self.SUPPORTED_VOICES)}"
            )

        # Ensure pipeline is loaded
        self._ensure_pipeline_loaded()

        try:
            import soundfile as sf
        except ImportError:
            raise RuntimeError(
                "soundfile package not installed. "
                "Please run: pip install soundfile"
            )

        try:
            print(f"Debug: Generating Kokoro audio for: '{text[:30]}...'")

            # Generate audio using the pipeline
            # The pipeline returns a generator of (graphemes, phonemes, audio) tuples
            generator = KokoroEngine._pipeline(text, voice=voice)

            # Collect all audio segments
            audio_segments = []
            sample_rate = 24000  # Kokoro uses 24kHz

            for graphemes, phonemes, audio in generator:
                audio_segments.append(audio)

            if not audio_segments:
                raise RuntimeError("Kokoro did not generate any audio")

            # Concatenate all segments
            import numpy as np
            full_audio = np.concatenate(audio_segments)

            # Write to WAV bytes
            wav_buffer = io.BytesIO()
            sf.write(wav_buffer, full_audio, sample_rate, format="WAV")
            wav_buffer.seek(0)
            return wav_buffer.getvalue()

        except Exception as e:
            raise RuntimeError(f"Kokoro synthesis failed: {e}")
