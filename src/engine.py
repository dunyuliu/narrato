"""TTS Engine abstraction and factory."""

from abc import ABC, abstractmethod
from typing import List, Tuple


class TTSEngine(ABC):
    """Abstract base class for TTS engines."""

    @abstractmethod
    def synthesize(self, text: str, voice: str) -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            voice: Voice/language identifier

        Returns:
            Audio bytes (MP3 format)
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get engine name."""
        pass

    @abstractmethod
    def get_supported_voices(self) -> List[str]:
        """Get list of supported voice/language codes."""
        pass

    @abstractmethod
    def get_voice_info(self) -> str:
        """Get human-readable voice/language info."""
        pass

    @abstractmethod
    def get_chunk_size(self) -> int:
        """Return recommended chunk size for this engine."""
        pass


class EngineFactory:
    """Factory for creating TTS engines."""

    _engines = {}
    _initialized = False

    @classmethod
    def _lazy_init(cls) -> None:
        """Lazy initialize engines to avoid circular imports."""
        if cls._initialized:
            return
        from .engines.gtts_engine import gTTSEngine  # noqa: E402
        from .engines.bark_engine import BarkEngine  # noqa: E402
        from .engines.gemini_engine import GeminiEngine  # noqa: E402
        from .engines.kokoro_engine import KokoroEngine  # noqa: E402

        cls._engines["gtts"] = gTTSEngine
        cls._engines["bark"] = BarkEngine
        cls._engines["gemini"] = GeminiEngine
        cls._engines["kokoro"] = KokoroEngine
        cls._initialized = True

    @classmethod
    def register(cls, name: str, engine_class: type) -> None:
        """Register an engine."""
        cls._lazy_init()
        cls._engines[name] = engine_class

    @classmethod
    def get_engine(cls, name: str) -> TTSEngine:
        """Get an engine instance by name."""
        cls._lazy_init()
        if name not in cls._engines:
            raise ValueError(
                f"Unknown engine: {name}. Available: {', '.join(cls._engines.keys())}"
            )
        return cls._engines[name]()

    @classmethod
    def list_engines(cls) -> List[str]:
        """List all available engines."""
        cls._lazy_init()
        return list(cls._engines.keys())

    @classmethod
    def get_default(cls) -> str:
        """Get the default engine name."""
        return "gtts"
