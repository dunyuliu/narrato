"""Tkinter GUI for Narrato document-to-speech converter."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import threading
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractor import extract_text
from src.chunker import chunk_text
from src.tts_client import text_to_speech
from src.concatenator import concatenate_audio
from src.engine import EngineFactory


class NarratoGUI:
    """GUI application for converting documents to speech."""

    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Narrato v0.0.2 - Document to Speech Converter")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        self.selected_file = None
        self.is_converting = False

        self._create_widgets()

    def _create_widgets(self):
        """Create GUI widgets."""
        # Title
        title_label = tk.Label(
            self.root,
            text="Narrato v0.0.2 - Document to Speech",
            font=("Arial", 22, "bold"),
            fg="black",
            pady=10,
        )
        title_label.pack()

        # File selection frame
        file_frame = ttk.LabelFrame(self.root, text="1. Select File", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        self.file_button = tk.Button(
            file_frame,
            text="Browse for .docx or .pdf file",
            command=self._select_file,
            width=30,
            bg="#4CAF50",
            fg="black",
            font=("Arial", 13, "bold"),
        )
        self.file_button.pack(side=tk.LEFT, padx=5)

        self.file_label = tk.Label(file_frame, text="No file selected", fg="black", font=("Arial", 12))
        self.file_label.pack(side=tk.LEFT, padx=5)

        # Settings frame
        settings_frame = ttk.LabelFrame(self.root, text="2. Settings", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)

        # Engine selection
        engine_frame = tk.Frame(settings_frame)
        engine_frame.pack(fill=tk.X, pady=5)

        tk.Label(engine_frame, text="TTS Engine:", fg="black", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.engine_var = tk.StringVar(value="gtts")
        engine_combo = ttk.Combobox(
            engine_frame,
            textvariable=self.engine_var,
            values=EngineFactory.list_engines(),
            state="readonly",
            width=15,
            font=("Arial", 11),
        )
        engine_combo.pack(side=tk.LEFT, padx=5)
        engine_combo.bind("<<ComboboxSelected>>", self._on_engine_changed)

        # Voice/Language selection
        voice_frame = tk.Frame(settings_frame)
        voice_frame.pack(fill=tk.X, pady=5)

        tk.Label(voice_frame, text="Voice/Language:", fg="black", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.voice_var = tk.StringVar(value="en")
        self.voice_combo = ttk.Combobox(
            voice_frame,
            textvariable=self.voice_var,
            state="readonly",
            width=15,
            font=("Arial", 11),
        )
        self.voice_combo.pack(side=tk.LEFT, padx=5)
        self._update_voices()

        # Speed selection
        speed_frame = tk.Frame(settings_frame)
        speed_frame.pack(fill=tk.X, pady=5)

        tk.Label(speed_frame, text="Speed:", fg="black", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.speed_var = tk.StringVar(value="1.2")
        speed_combo = ttk.Combobox(
            speed_frame,
            textvariable=self.speed_var,
            values=["0.75", "1.0", "1.2", "1.5", "2.0"],
            state="readonly",
            width=15,
            font=("Arial", 11),
        )
        speed_combo.pack(side=tk.LEFT, padx=5)

        # All speeds option
        self.all_speeds_var = tk.BooleanVar(value=False)
        all_speeds_check = tk.Checkbutton(
            settings_frame,
            text="Generate all speeds (1.0x, 1.2x, 1.5x)",
            variable=self.all_speeds_var,
            fg="black",
            font=("Arial", 12),
        )
        all_speeds_check.pack(anchor=tk.W, padx=5, pady=5)

        # Slow speech option
        self.slow_var = tk.BooleanVar(value=False)
        slow_check = tk.Checkbutton(
            settings_frame,
            text="Speak slower",
            variable=self.slow_var,
            fg="black",
            font=("Arial", 12),
        )
        slow_check.pack(anchor=tk.W, padx=5, pady=5)

        # Workers
        workers_frame = tk.Frame(settings_frame)
        workers_frame.pack(fill=tk.X, pady=5)

        tk.Label(workers_frame, text="Concurrent workers:", fg="black", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.workers_var = tk.StringVar(value="1")
        workers_spin = tk.Spinbox(
            workers_frame,
            from_=1,
            to=20,
            textvariable=self.workers_var,
            width=5,
        )
        workers_spin.pack(side=tk.LEFT, padx=5)

        # Convert button
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        self.convert_button = tk.Button(
            button_frame,
            text="Convert to MP3",
            command=self._start_conversion,
            bg="#2196F3",
            fg="black",
            font=("Arial", 14, "bold"),
            height=2,
        )
        self.convert_button.pack(fill=tk.X)

        # Progress bar
        self.progress = ttk.Progressbar(
            self.root, mode="indeterminate", length=300
        )
        self.progress.pack(fill=tk.X, padx=10, pady=5)

        # Status text
        status_label = tk.Label(
            self.root, text="Status:", fg="black", font=("Arial", 13, "bold")
        )
        status_label.pack(anchor=tk.W, padx=10, pady=(10, 0))

        self.status_text = tk.Text(
            self.root, height=8, width=60, wrap=tk.WORD, state=tk.DISABLED,
            fg="black", font=("Arial", 11)
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbar for text
        scrollbar = ttk.Scrollbar(self.status_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.status_text.yview)

    def _select_file(self):
        """Open file dialog to select a document file."""
        file_path = filedialog.askopenfilename(
            title="Select a document (.docx or .pdf)",
            filetypes=[("Word Documents", "*.docx"), ("PDF Files", "*.pdf"), ("All Files", "*.*")],
        )

        if file_path:
            self.selected_file = file_path
            file_name = Path(file_path).name
            self.file_label.config(text=file_name, fg="green")

    def _add_status(self, message):
        """Add a message to the status text."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()

    def _clear_status(self):
        """Clear the status text."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)

    def _on_engine_changed(self, event=None):
        """Update voice options when engine is changed."""
        self._update_voices()

    def _update_voices(self):
        """Update available voices based on selected engine."""
        engine_name = self.engine_var.get()
        engine = EngineFactory.get_engine(engine_name)
        voices = engine.get_supported_voices()
        self.voice_combo.config(values=voices)
        self.voice_combo.current(0)

    def _start_conversion(self):
        """Start the conversion in a separate thread."""
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a file first")
            return

        if self.is_converting:
            messagebox.showwarning("Warning", "Conversion already in progress")
            return

        # Check for Gemini API key if Gemini engine is selected
        if self.engine_var.get() == "gemini":
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                # Prompt user for API key
                api_key = simpledialog.askstring(
                    "Gemini API Key Required",
                    "Please enter your Gemini API Key:\n(Get one at ai.google.dev)",
                    parent=self.root
                )
                if api_key:
                    os.environ["GEMINI_API_KEY"] = api_key.strip()
                else:
                    self._add_status("✗ Conversion cancelled: Gemini API Key required.")
                    return

        self.is_converting = True
        self.convert_button.config(state=tk.DISABLED)
        self._clear_status()
        self._add_status("Starting conversion...")
        self.progress.start()

        # Run conversion in a separate thread to avoid freezing GUI
        thread = threading.Thread(target=self._convert_worker)
        thread.daemon = True
        thread.start()

    def _convert_worker(self):
        """Worker thread for conversion."""
        try:
            input_path = self.selected_file
            output_path = str(Path(input_path).with_suffix(".mp3"))
            engine_name = self.engine_var.get()
            voice = self.voice_var.get()
            speed = float(self.speed_var.get())
            all_speeds = self.all_speeds_var.get()
            slow = self.slow_var.get()
            workers = int(self.workers_var.get())

            self._add_status(f"Reading: {Path(input_path).name}")
            text = extract_text(input_path)
            self._add_status(f"Extracted {len(text)} characters")

            # Get chunk size from engine
            engine = EngineFactory.get_engine(engine_name)
            chunk_size = engine.get_chunk_size()

            self._add_status(f"Chunking text (limit: {chunk_size} chars)...")
            chunks = chunk_text(text, max_chunk_size=chunk_size)
            self._add_status(f"Created {len(chunks)} chunks")

            # Create a directory for parts
            parts_dir = Path(output_path).with_suffix("")
            parts_dir = str(parts_dir) + "_parts"
            os.makedirs(parts_dir, exist_ok=True)
            self._add_status(f"Saving temporary chunks to: {Path(parts_dir).name}")

            self._add_status(
                f"Generating speech (engine: {engine_name}, voice: {voice}, speed: {'slow' if slow else 'normal'})..."
            )
            mp3_blobs = text_to_speech(
                chunks, 
                engine_name=engine_name, 
                voice=voice, 
                workers=workers, 
                slow=slow,
                output_dir=parts_dir
            )

            if all_speeds:
                # Generate all 3 speeds
                speeds = [1.0, 1.2, 1.5]
                base_path = str(Path(output_path).with_suffix(""))

                for sp in speeds:
                    speed_output = f"{base_path}_{sp}x.mp3"
                    self._add_status(f"Creating {sp}x version...")
                    concatenate_audio(mp3_blobs, speed_output, speed=sp)
                    self._add_status(f"✓ Saved: {Path(speed_output).name}")

                self._add_status("\n✓ Conversion complete! Created 3 versions:")
                for sp in speeds:
                    speed_output = f"{base_path}_{sp}x.mp3"
                    self._add_status(f"  - {Path(speed_output).name}")

            else:
                # Generate single version
                self._add_status("Concatenating audio...")
                concatenate_audio(mp3_blobs, output_path, speed=speed)
                self._add_status(f"\n✓ Conversion complete!")
                self._add_status(f"Saved to: {Path(output_path).name}")

            messagebox.showinfo("Success", "Conversion completed successfully!")

        except Exception as e:
            self._add_status(f"\n✗ Error: {e}")
            messagebox.showerror("Conversion Error", str(e))

        finally:
            self.is_converting = False
            self.convert_button.config(state=tk.NORMAL)
            self.progress.stop()


def main():
    """Run the GUI application."""
    root = tk.Tk()
    app = NarratoGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
