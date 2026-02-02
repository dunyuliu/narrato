#!/bin/bash
# Setup script for Narrato with virtual environment

set -e

echo "🎙️  Narrato Setup"
echo "==============="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python $PYTHON_VERSION"

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo ""
    echo "⚠️  ffmpeg not found. Installing..."
    if command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "❌ Please install ffmpeg manually:"
        echo "   macOS: brew install ffmpeg"
        echo "   Ubuntu: sudo apt-get install ffmpeg"
        echo "   Windows: choco install ffmpeg"
        exit 1
    fi
fi
echo "✓ ffmpeg installed"

# Create virtual environment
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "📥 Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1

# Install requirements
echo "📥 Installing Narrato dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Activate venv: source venv/bin/activate"
echo "   2. Try CLI: python -m narrato --help"
echo "   3. Try GUI: python gui_launcher.py"
echo ""
echo "🚀 Quick start:"
echo "   python -m narrato document.docx"
echo "   python -m narrato document.docx --engine bark --voice en_speaker_0"
