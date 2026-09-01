import os, sys, subprocess, tkinter as tk
from shutil import which
from tkinter import filedialog, messagebox, ttk

ffmpeg = which("ffmpeg")

if ffmpeg is None:
    print("Error: FFmpeg was not found in PATH.")
    sys.exit(1)

valid_extensions = (".mp3", ".wav", ".flac", ".aac", ".ogg")

audio_paths = []
invalid_paths = []

def scan_directory(path, recursive):
    for root, _, files in os.walk(path):
        for filename in files:
            file_path = os.path.join(root, filename)
            abs_path = os.path.abspath(file_path)

            if os.path.splitext(filename)[1].lower() in valid_extensions:
                audio_paths.append(abs_path)
            else:
                invalid_paths.append(abs_path)

        if not recursive:
            break

for path in sys.argv[1:]:
    if os.path.isfile(path):
        if os.path.splitext(path)[1].lower() in valid_extensions:
            audio_paths.append(os.path.abspath(path))

    elif os.path.isdir(path):
        scan_subdirectories = messagebox.askyesno("Scan Subdirectories", f"Would you like to scan subdirectories inside:\n\n{os.path.abspath(path)}?")
        scan_directory(path, scan_subdirectories)

audio_paths = list(dict.fromkeys(audio_paths))
invalid_paths = list(dict.fromkeys(invalid_paths))

if not audio_paths:
    import_dir = messagebox.askyesno("Import Options", "Would you prefer importing an entire directory?\n\nYes — Directory\nNo — Individual Files")

    if import_dir:
        dir_path = filedialog.askdirectory(title="Select input folder")

        if not dir_path:
            sys.exit(0)

        audio_paths = []
        invalid_paths = []

        scan_subdirectories = messagebox.askyesno("Scan Subdirectories", "Would you like to scan subdirectories inside the selected folder?")

        scan_directory(dir_path, scan_subdirectories)

    else:
        audio_paths = list(filedialog.askopenfilenames(title="Select audio files", filetypes=[("Audio files", "*.mp3 *.wav *.flac *.aac *.ogg")]))

if not audio_paths:
    sys.exit(0)

if invalid_paths:
    messagebox.showinfo("Invalid Files Detected", "Note that some files are not audio files.\nOnly the audio files will be converted into OGG.")

# Gain change prompt
gain_root = tk.Tk()
gain_root.title("Gain Change")
gain_root.resizable(False, False)

gain_value = tk.StringVar(value="0")

tk.Label(gain_root, text="Gain Change Level").pack(padx=20, pady=(15, 5))

gain_spinbox = ttk.Spinbox(gain_root, from_=-100.0, to=100.0, increment=0.1, textvariable=gain_value, width=15)
gain_spinbox.pack(padx=20, pady=5)

def validate_gain(value):
    try:
        float(value)
        return True
    except ValueError:
        return value in ("", "-", ".", "-.")

gain_spinbox.config(validate="key", validatecommand=(gain_root.register(validate_gain), "%P"))

def ready():
    try:
        float(gain_value.get())
    except ValueError:
        messagebox.showerror("Invalid Gain", "Please enter a valid integer or decimal number.", parent=gain_root)
        return

    gain_root.destroy()

ttk.Button(gain_root, text="Ready!", command=ready).pack(padx=20, pady=(5, 15))

gain_root.protocol("WM_DELETE_WINDOW", sys.exit)
gain_root.grab_set()
gain_root.wait_window()

gain_db = float(gain_value.get())

if len(audio_paths) >= 2:
    output_dir = filedialog.askdirectory(title="Select output folder")

    if not output_dir:
        sys.exit(0)

    prefix_filename = messagebox.askyesno("Filename Prefix", "Allow the script to add directory names as a filename prefix?\n\nExample:\nDir1/Dir2/BaseFilename.mp3 → Dir1_Dir2_BaseFilename.ogg")

    common_dir = os.path.commonpath(audio_paths)

    if not os.path.isdir(common_dir):
        common_dir = os.path.dirname(common_dir)

    total = len(audio_paths)
    index = 0

    for audio_path in audio_paths:
        base_name = os.path.splitext(os.path.basename(audio_path))[0]

        if prefix_filename:
            relative_dir = os.path.relpath(os.path.dirname(audio_path), common_dir)

            if relative_dir != ".":
                prefix = "_".join(part for part in relative_dir.split(os.sep) if part not in ("", "."))

                if prefix:
                    base_name = f"{prefix}_{base_name}"

        output_path = os.path.join(output_dir, base_name + ".ogg")
        print(f"Converting {index + 1}/{len(audio_paths)}: {os.path.basename(audio_path)}")

        try:
            subprocess.run([ffmpeg, "-loglevel", "quiet", "-i", audio_path, "-af", f"volume={gain_db}dB", "-c:a", "libvorbis", "-q:a", "10", "-y", output_path], check=True)

            print(f"Success converting {os.path.basename(audio_path)}")
            index += 1

        except subprocess.CalledProcessError:
            print(f"Failed converting {os.path.basename(audio_path)}")
            total -= 1

    print(f"Output: {output_dir}")

else:
    output_path = filedialog.asksaveasfilename(title="Save OGG file", defaultextension=".ogg", filetypes=[("OGG files", "*.ogg")])

    if not output_path:
        sys.exit(0)

    try:
        subprocess.run([ffmpeg, "-loglevel", "quiet", "-i", audio_paths[0], "-af", f"volume={gain_db}dB", "-c:a", "libvorbis", "-q:a", "10", "-y", output_path], check=True)
        print(f"Conversion successful: {output_path}")

    except subprocess.CalledProcessError:
        print(f"Conversion failed: {audio_paths[0]}")