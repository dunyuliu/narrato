"""Source code for docx2mp3."""

# Enable Metal GPU support on Apple Silicon for Bark TTS
import os
if not os.environ.get("SUNO_ENABLE_MPS"):
    os.environ["SUNO_ENABLE_MPS"] = "True"
