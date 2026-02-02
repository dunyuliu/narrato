"""Bark TTS engine."""

import os
import functools
import tempfile
from typing import List

from scipy.io.wavfile import write as write_wav
import numpy as np

from ..engine import TTSEngine


class BarkEngine(TTSEngine):
    """Bark TTS engine (runs locally, open-source)."""

    # Supported voices (speaker IDs)
    SUPPORTED_VOICES = [
        "en_speaker_0", "en_speaker_1", "en_speaker_2", "en_speaker_3",
        "en_speaker_4", "en_speaker_5", "en_speaker_6", "en_speaker_7",
        "en_speaker_8", "en_speaker_9",
    ]

    def get_name(self) -> str:
        """Get engine name."""
        return "Bark TTS (Local)"

    def get_supported_voices(self) -> List[str]:
        """Get supported speaker voices."""
        return self.SUPPORTED_VOICES.copy()

    def get_voice_info(self) -> str:
        """Get voice information."""
        return "Speaker IDs: en_speaker_0 through en_speaker_9"

    def get_chunk_size(self) -> int:
        """Return recommended chunk size for this engine."""
        return 160

    # Global flag to track if models are loaded
    _models_loaded = False

    def _ensure_models_loaded(self):
        """Lazy load Bark models and apply patches exactly like test_bark.py."""
        if self._models_loaded:
            return

        print("Debug: Initializing Bark engine...")

        # Enable Mac optimizations BEFORE importing bark
        os.environ["SUNO_ENABLE_MPS"] = "True"
        os.environ["SUNO_OFFLOAD_CPU"] = "True"

        # Lazy import torch and bark
        global torch, generate_audio, preload_models, SAMPLE_RATE
        import torch
        from bark import generate_audio, preload_models, SAMPLE_RATE

        # Monkey patch torch.load to default weights_only=False
        # This is required because bark models were saved with older numpy/torch
        # and PyTorch 2.6+ defaults to weights_only=True, which fails with Numpy 2.x types.
        _original_load = torch.load

        @functools.wraps(_original_load)
        def _safe_load(*args, **kwargs):
            if 'weights_only' not in kwargs:
                kwargs['weights_only'] = False
            return _original_load(*args, **kwargs)

        torch.load = _safe_load

        print("Debug: Preloading Bark models (this may take a while on first run)...")
        preload_models()
        self._models_loaded = True
        print("Debug: Bark models loaded.")

    def synthesize(self, text: str, voice: str) -> bytes:
        """
        Synthesize speech using Bark TTS.

        Args:
            text: Text to speak
            voice: Speaker ID (e.g., "en_speaker_0")

        Returns:
            MP3 audio bytes (as WAV since Bark outputs WAV)
        """
        if voice not in self.SUPPORTED_VOICES:
            raise ValueError(
                f"Unsupported voice: {voice}. "
                f"Supported: {', '.join(self.SUPPORTED_VOICES)}"
            )

        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_file = tmp.name

        try:
            # Ensure models are loaded and patched
            self._ensure_models_loaded()

            print(f"Debug: Generating Bark audio for: '{text[:20]}...'")
            
            # Generate audio (returns numpy array)
            audio_array = generate_audio(text, history_prompt=voice)

            # Save to WAV file
            write_wav(wav_file, SAMPLE_RATE, audio_array)

            # Read WAV file bytes to return
            with open(wav_file, "rb") as f:
                return f.read()

        except Exception as e:
            raise RuntimeError(f"Bark synthesis failed: {e}")

        finally:
            if os.path.exists(wav_file):
                os.remove(wav_file)

