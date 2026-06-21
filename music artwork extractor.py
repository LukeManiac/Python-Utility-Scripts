import os, io, sys
from tkinter import filedialog, messagebox
from mutagen import File
from mutagen.id3 import APIC
from mutagen.wave import WAVE
from PIL import Image

file_paths = sys.argv[1:] if len(sys.argv) > 1 else filedialog.askopenfilenames(title="Select Audio Files", filetypes=[("All Audio Files", "*.mp3 *.flac *.wav *.ogg *.m4a *.aac *.wma *.alac *.aiff *.mp2 *.ac3"),("MP3 Audio", "*.mp3"),("FLAC Audio", "*.flac"),("Waveform Audio (WAV)", "*.wav"),("Ogg Vorbis Audio", "*.ogg"),("MPEG-4 Audio (M4A)", "*.m4a"),("AAC Audio", "*.aac"),("WMA Audio", "*.wma"),("Apple Lossless (ALAC)", "*.alac"),("AIFF Audio", "*.aiff"),("MPEG-2 Audio (MP2)", "*.mp2"),("AC-3 Audio", "*.ac3"),("All Files", "*.*")])

if file_paths:
    valid_files = []
    invalid_files = []

    for file in file_paths:
        (valid_files if os.path.splitext(file)[1].lower() in {'.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac', '.wma', '.alac', '.aiff', '.mp2', '.ac3'} else invalid_files).append(file)

    if invalid_files:
        file_paths = valid_files

        if not messagebox.askyesno("Non-Audio Files Detected", f"The files below have an extension that isn't an audio file extension:\n\n{"\n".join(invalid_files)}\n\nProceed?"):
            file_paths = invalid_files

    save_directory = filedialog.askdirectory(title="Select folder to save artworks")

    if save_directory:
        file_names = []

        for file_path in file_paths:
            try:
                audio: WAVE = File(file_path)

                if audio is None or not hasattr(audio, 'tags'):
                    messagebox.showerror("Error", f"Unsupported or untagged file:\n{file_path}")
                    continue

                for tag in audio.tags.values():
                    if isinstance(tag, APIC):
                        music_name = os.path.splitext(os.path.basename(file_path))[0]
                        file_names.append(music_name)
                        Image.open(io.BytesIO(tag.data)).save(os.path.join(save_directory, f"{music_name}.png"), format="PNG")
                        break
                else:
                    messagebox.showwarning("No artwork", f"No artwork found in:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error processing {file_path}:\n{e}")
        
        messagebox.showinfo("Complete", f"Successfully exported {len(file_names)} artwork file(s):\n\n" + "\n".join(file_names) if file_names else "No artworks were found in the selected files.")
    else:
        messagebox.showerror("No output folder selected", "Rerun the script and choose a folder.")
else:
    messagebox.showerror("No files selected", "Rerun the script and select one or more audio files.")