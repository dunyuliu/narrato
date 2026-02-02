#!/usr/bin/env python3
"""Setup script for Narrato with optional dependencies."""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and show status."""
    print(f"  {description}...", end=" ", flush=True)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        print("✓")
        return True
    except subprocess.CalledProcessError as e:
        print("✗")
        print(f"    Error: {e.stderr}")
        return False

def main():
    """Setup Narrato."""
    print("🎙️  Narrato Setup")
    print("=" * 40)
    print()

    # Check Python
    print("Checking Python...")
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if sys.version_info < (3, 8):
        print(f"✗ Python 3.8+ required (you have {py_version})")
        sys.exit(1)
    print(f"  ✓ Python {py_version}")
    print()

    # Upgrade pip
    print("Upgrading pip...")
    run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Updating pip"
    )
    print()

    # Install base requirements
    print("Installing Narrato...")
    requirements = Path(__file__).parent / "requirements.txt"
    run_command(
        f"{sys.executable} -m pip install -r {requirements}",
        "Installing base dependencies"
    )
    print()

    # Optional: Bark
    print("Optional: Bark TTS (local, high-quality)")
    print("  Install with: pip install bark-ml")
    print("  (Requires SDL2: brew install sdl2)")
    print()

    print("✅ Setup complete!")
    print()
    print("🚀 Try Narrato:")
    print("   python -m narrato document.docx")
    print("   python -m narrato document.docx --engine bark")
    print("   python gui_launcher.py")

if __name__ == "__main__":
    main()
