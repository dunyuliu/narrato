# Changelog

All notable changes to Narrato will be documented in this file.

## [0.0.2] - 2025-02-01

### Fixed
- Added missing `scipy` dependency (required for Bark engine)
- Fixed tkinter support for Python 3.12

### Changed
- Moved CLAUDE.md to project root
- Requires Python 3.12 (Python 3.13 not yet compatible with Kokoro dependencies)

## [0.0.1] - 2025-02-01

### Added
- Initial release of Narrato document-to-speech converter
- CLI tool (`python -m src.cli`) for converting .docx and .pdf files to MP3
- GUI application (`python -m gui.app`) with Tkinter interface
- Four TTS engine options:
  - **gTTS**: Google Text-to-Speech (fast, cloud-based, 30+ languages)
  - **Bark**: Suno Bark TTS (local, AI-generated voices)
  - **Gemini**: Google Gemini AI voices (cloud, premium quality)
  - **Kokoro**: High-quality local TTS with natural prosody (11 voices)
- Smart text chunking that respects sentence boundaries
- Concurrent processing with configurable worker threads
- Speed adjustment (0.75x to 2.0x playback speed)
- Multi-speed output option (generates 1.0x, 1.2x, 1.5x versions)
- Lossless MP3 concatenation using ffmpeg

### Engines

| Engine | Type | Voices | Chunk Size |
|--------|------|--------|------------|
| gTTS | Cloud | 30+ languages | 4096 chars |
| Bark | Local | 10 speakers | 160 chars |
| Gemini | Cloud | 5 voices | 4096 chars |
| Kokoro | Local | 11 voices | 500 chars |

### Dependencies
- python-docx for .docx extraction
- PyPDF2 for .pdf extraction
- gtts for Google TTS
- google-generativeai for Gemini
- kokoro and soundfile for Kokoro TTS
- ffmpeg for audio concatenation
