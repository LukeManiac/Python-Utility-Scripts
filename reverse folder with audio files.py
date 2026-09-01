import os, shutil
from tkinter import filedialog, messagebox
from pydub import AudioSegment
from mutagen import File

# Supported audio extensions
AUDIO_EXTS = (".mp3", ".wav", ".ogg", ".flac")

messagebox.showinfo("Before you proceed...", "If you want to end the process, just close the input directory dialog. Same goes for output directory dialog.")

while True:
    input_dir = filedialog.askdirectory(title="Select input directory")

    if not input_dir:
        exit()

    audio_files = []

    if bool(messagebox.askyesnocancel("Include Subfolders", "Do you want to sync subfolders too?")):
        for root_dir, dirs, files in os.walk(input_dir):
            for file in files:
                if file.lower().endswith(AUDIO_EXTS):
                    full_path = os.path.join(root_dir, file)
                    audio_files.append(full_path)
    else:
        for file in os.listdir(input_dir):
            full_path = os.path.join(input_dir, file)

            if os.path.isfile(full_path) and file.lower().endswith(AUDIO_EXTS):
                audio_files.append(full_path)

    if not audio_files:
        messagebox.showwarning("No Audio Files", "No supported audio files were found in this folder. Please select another directory.")
        continue

    break

while True:
    output_dir = filedialog.askdirectory(title="Select output directory")

    if not output_dir:
        exit()

    if os.path.abspath(output_dir) == os.path.abspath(input_dir):
        messagebox.showerror("Invalid Directory", "The input directory cannot be the same as the output directory.")
        continue

    break

file_count = len(audio_files)

if os.path.exists(output_dir):
    shutil.rmtree(output_dir)

os.makedirs(output_dir)

for idx, path in enumerate(audio_files):
    rel_path = os.path.relpath(path, input_dir)
    output_path = os.path.join(output_dir, rel_path)

    print(f"Processing file: {rel_path}")

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        stat = os.stat(path)
        reversed_audio = AudioSegment.from_file(path).reverse()
        reversed_audio.export(output_path, format=os.path.splitext(output_path)[1][1:].lower())
        src_tags = File(path, easy=False)
        dst_tags = File(output_path, easy=False)

        if src_tags and dst_tags:
            dst_tags.clear()

            for key in src_tags.keys():
                dst_tags[key] = src_tags[key]

            dst_tags.save()

        os.utime(output_path, (stat.st_atime, stat.st_mtime))
        print(f"Currently processed {idx + 1} out of {file_count} audio files!")

    except Exception as e:
        print(f"Failed to process {path}: {e}")

print("All audio files have been reversed and saved.")