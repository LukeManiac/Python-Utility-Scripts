import os, subprocess
from shutil import which
from tkinter import filedialog, messagebox

choice = messagebox.askyesno("Select Input", "Do you want to import files?\n\nYes = Select files\nNo = Select a directory")
video_extensions = (".mp4", ".mkv", ".mov", ".webm", ".avi")

if choice:
    input_paths = filedialog.askopenfilenames(title="Select Video(s)", filetypes=[("Video Files", "*.mp4 *.mkv *.mov *.webm *.avi"), ("All Files", "*.*")])

    if not input_paths:
        raise SystemExit

    recursive = False

else:
    input_directory = filedialog.askdirectory(title="Select Input Directory")

    if not input_directory:
        raise SystemExit

    recursive = messagebox.askyesno("Recursive Scanning", "Do you want to scan subdirectories recursively?")
    input_paths = []

    if recursive:
        for root, _, files in os.walk(input_directory):
            for file in files:
                if os.path.splitext(file)[1].lower() in video_extensions:
                    input_paths.append(os.path.join(root, file))

    else:
        for file in os.listdir(input_directory):
            input_path = os.path.join(input_directory, file)

            if os.path.isfile(input_path) and os.path.splitext(file)[1].lower() in video_extensions:
                input_paths.append(input_path)

    if not input_paths:
        messagebox.showinfo("No Videos Found", "No supported video files were found.")
        raise SystemExit

if len(input_paths) == 1:
    input_path = input_paths[0]
    base_name = os.path.basename(input_path)
    name, ext = os.path.splitext(base_name)

    output_path = filedialog.asksaveasfilename(title="Save Converted Video", initialfile=base_name, defaultextension=ext, filetypes=[("MP4", "*.mp4"), ("MKV", "*.mkv"), ("MOV", "*.mov"), ("WEBM", "*.webm"), ("AVI", "*.avi"), ("All Files", "*.*")])

    if not output_path:
        raise SystemExit

    output_paths = [output_path]

else:
    output_directory = filedialog.askdirectory(title="Select Output Directory")

    if not output_directory:
        raise SystemExit

    output_paths = []

    for input_path in input_paths:
        if recursive:
            output_path = os.path.join(output_directory, os.path.relpath(input_path, input_directory))

        else:
            output_path = os.path.join(output_directory, os.path.basename(input_path))

        output_paths.append(output_path)

ffmpeg = which("ffmpeg")

if not ffmpeg:
    messagebox.showerror("Error", "FFmpeg was not found. Please install FFmpeg and add it to PATH.")
    raise SystemExit

successful = []
failed = []

print(f"Found {len(input_paths)} video(s) to process.\n")

for index, (input_path, output_path) in enumerate(zip(input_paths, output_paths), 1):
    output_folder = os.path.dirname(output_path)

    if output_folder:
        os.makedirs(output_folder, exist_ok=True)

    command = [ffmpeg, "-i", input_path, "-c:v", "libx264", "-c:a", "aac", "-map", "0", "-movflags", "+faststart", "-y", output_path]

    print(f"[{index}/{len(input_paths)}] Processing: {input_path}")

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

        print(f"[{index}/{len(input_paths)}] SUCCESS: {input_path}")
        print(f"Output: {output_path}\n")

        successful.append((input_path, output_path))

    except subprocess.CalledProcessError as e:
        error = e.stderr[-4000:] if e.stderr else "Unknown FFmpeg error."

        print(f"[{index}/{len(input_paths)}] FAILED: {input_path}")
        print(f"FFmpeg error:\n{error}\n")

        failed.append((input_path, output_path, error))

if failed:
    failed_text = "\n\n".join([f"{os.path.basename(input_path)}\n{error}" for input_path, output_path, error in failed])

    print("========== PROCESS COMPLETE ==========")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print("======================================")

    messagebox.showwarning("Process Complete", f"Completed: {len(successful)}\nFailed: {len(failed)}\n\nFailed Files:\n\n{failed_text}")

else:
    print("========== PROCESS COMPLETE ==========")
    print(f"Successful: {len(successful)}")
    print("Failed: 0")
    print("======================================")

    messagebox.showinfo("Process Complete", f"{len(successful)} video(s) successfully re-encoded to H.264/AAC.")