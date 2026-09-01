import os, shutil, subprocess, platform, threading, queue, tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional
from urllib.parse import urlparse

AUDIO_EXTENSIONS = {
    ".mp3": "mp3",
    ".m4a": "m4a",
    ".flac": "flac",
    ".wav": "wav",
    ".ogg": "vorbis",
}

VIDEO_EXTENSIONS = {
    ".mp4": "mp4",
    ".mkv": "mkv",
    ".webm": "webm",
    ".mov": "mov",
    ".avi": "avi",
}

last_path = None
selected_video_extension = ".mp4"
progress_queue = queue.Queue()

add_button = None
delete_button = None
bulk_window = None
bulk_progress = None
bulk_status_label = None
bulk_download_button = None

def process_progress_queue():
    try:
        while True:
            message = progress_queue.get_nowait()

            if message[0] == "progress":
                percentage, current, total = message[1:]

                if total:
                    progress = ((current - 1) + percentage / 100) / total * 100
                    playlist_progress.config(value=progress)
                    status_label.config(text=f"Downloading playlist...\nFile {current} of {total} — {percentage:.1f}%")

            elif message[0] == "status":
                status_label.config(text=message[1])

            elif message[0] == "complete":
                folder = message[1]
                failed_items = message[2] if len(message) > 2 else []

                playlist_progress.config(value=100)
                download_button.state(["!disabled"])
                playlist_progress.grid_remove()

                if failed_items:
                    status_label.config(text=f"Playlist download complete — {len(failed_items)} error(s).")
                    error_text = "\n\n".join(failed_items[:20])

                    if len(failed_items) > 20:
                        error_text += f"\n\n...and {len(failed_items) - 20} more."

                    messagebox.showwarning("Playlist completed with errors", f"The playlist finished downloading, but some items could not be downloaded.\n\nSaved to:\n{folder}\n\nErrors:\n{error_text}")

                else:
                    status_label.config(text="Playlist download complete.")
                    messagebox.showinfo("Complete", f"Playlist download complete!\n\nSaved to:\n{folder}")

            elif message[0] == "error":
                status_label.config(text="Playlist download failed.")
                download_button.state(["!disabled"])
                playlist_progress.grid_remove()
                messagebox.showerror("Download failed", message[1])

            elif message[0] == "regular_progress":
                percentage = message[1]
                playlist_progress.config(value=percentage)
                playlist_progress.grid()
                status_label.config(text=f"Downloading...\n{percentage:.1f}%")

            elif message[0] == "regular_complete":
                global last_path

                save_path = message[1]
                last_path = save_path

                playlist_progress.config(value=100)
                status_label.config(text="Download complete.")
                download_button.state(["!disabled"])
                open_button.state(["!disabled"])
                messagebox.showinfo("Complete", f"Download complete!\n\nSaved to:\n{save_path}")
                playlist_progress.grid_remove()

            elif message[0] == "regular_error":
                status_label.config(text="Download failed.")
                download_button.state(["!disabled"])
                open_button.state(["disabled"])
                playlist_progress.grid_remove()
                messagebox.showerror("Download failed", message[1])

            elif message[0] == "bulk_progress":
                percentage, current, total = message[1:]
                progress = ((current - 1) + percentage / 100) / total * 100

                if bulk_window is not None and bulk_window.winfo_exists():
                    bulk_progress.config(value=progress)
                    bulk_progress.pack(pady=5)
                    bulk_status_label.config(text=f"Bulk downloading...\nVideo {current} of {total} — {percentage:.1f}%")

            elif message[0] == "bulk_item_error":
                if bulk_window is not None and bulk_window.winfo_exists():
                    bulk_status_label.config(text=message[1])

            elif message[0] == "bulk_complete":
                folder = message[1]
                failed_urls = message[2]

                if bulk_window is not None and bulk_window.winfo_exists():
                    bulk_progress.config(value=100)

                    bulk_download_button.state(["!disabled"])
                    add_button.state(["!disabled"])
                    delete_button.state(["!disabled"])

                    bulk_progress.pack_forget()

                    if failed_urls:
                        bulk_status_label.config(text=f"Bulk download complete — {len(failed_urls)} video(s) failed.")
                        messagebox.showwarning("Bulk download completed with errors", f"Bulk download finished, but {len(failed_urls)} video(s) could not be downloaded.\n\nSuccessfully downloaded videos were saved to:\n{folder}\n\nFailed videos:\n{"\n\n".join(f"{index}. {url}" for index, url in enumerate(failed_urls, start=1))}", parent=bulk_window)

                    else:
                        bulk_status_label.config(text="Bulk download complete.")
                        messagebox.showinfo("Complete", f"Bulk download complete!\n\nSaved to:\n{folder}", parent=bulk_window)

            elif message[0] == "bulk_error":
                if bulk_window is not None and bulk_window.winfo_exists():
                    bulk_status_label.config(text="Bulk download failed.")
                    bulk_progress.pack_forget()
                    bulk_download_button.state(["!disabled"])
                    add_button.state(["!disabled"])
                    delete_button.state(["!disabled"])
                    messagebox.showerror("Bulk download failed", message[1], parent=bulk_window)

    except queue.Empty:
        pass

    root.after(50, process_progress_queue)

def find_executable(name: str) -> str:
    path = shutil.which(name)

    if path:
        return path

    raise FileNotFoundError(f"{name} was not found on PATH.")

def open_file():
    if not last_path or not os.path.exists(last_path):
        return

    system = platform.system()

    if system == "Windows":
        os.startfile(last_path)
    elif system == "Darwin":
        subprocess.run(["open", last_path])
    else:
        subprocess.run(["xdg-open", last_path])

def choose_format(parent: Optional[tk.Misc | tk.Tk] = None) -> str:
    global selected_video_extension

    format_window = tk.Toplevel(parent or root)
    format_window.title("Choose Format")
    format_window.resizable(False, False)
    format_window.transient(parent or root)
    format_window.grab_set()

    frame = ttk.Frame(format_window, padding=12)
    frame.pack()

    ttk.Label(frame, text="Choose format:").pack(pady=(0, 6))

    formats = list(AUDIO_EXTENSIONS.keys()) + list(VIDEO_EXTENSIONS.keys())
    format_var = tk.StringVar(value=selected_video_extension)

    format_dropdown = ttk.Combobox(frame, textvariable=format_var, values=formats, state="readonly", width=12)
    format_dropdown.pack()

    def confirm():
        global selected_video_extension

        selected_video_extension = format_var.get().lower()
        format_window.grab_release()
        format_window.destroy()

    def cancel():
        format_window.grab_release()
        format_window.destroy()

    ttk.Button(frame, text="Download", command=confirm).pack(pady=(10, 0))
    format_window.protocol("WM_DELETE_WINDOW", cancel)
    format_window.wait_window()

    return selected_video_extension

def is_playlist(url: str) -> bool:
    return "playlist?list=" in url.lower()

def invalid_extension(extension: str) -> bool:
    return extension.lower() not in VIDEO_EXTENSIONS and extension.lower() not in AUDIO_EXTENSIONS

def download_playlist(url: str):
    download_button.state(["disabled"])
    status_label.config(text="Choose playlist download folder...")

    folder = filedialog.askdirectory(title="Choose playlist download folder")

    if not folder:
        download_button.state(["!disabled"])
        status_label.config(text="")
        return

    selected_extension = choose_format(root)

    if not selected_extension:
        download_button.state(["!disabled"])
        status_label.config(text="")
        return

    extension = selected_extension.lower()

    if invalid_extension(extension):
        messagebox.showerror("Invalid format", "Please choose a supported format.")
        download_button.state(["!disabled"])
        return

    status_label.config(text="Starting playlist download...")
    playlist_progress.config(value=0)
    playlist_progress.grid()

    threading.Thread(target=download_playlist_worker, args=(url, folder, extension), daemon=True).start()

def download_playlist_worker(url: str, folder: str, extension: str):
    try:
        yt_dlp = find_executable("yt-dlp")
        ffmpeg = find_executable("ffmpeg")

        common_options = [yt_dlp, "--ignore-errors", "--no-abort-on-error", "--yes-playlist", "--ffmpeg-location", ffmpeg, "-o", os.path.join(folder, "%(title)s.%(ext)s"), url]

        if extension in VIDEO_EXTENSIONS:
            command = [*common_options[:-1], "-f", "bestvideo+bestaudio/best", "--merge-output-format", extension[1:], "--postprocessor-args", "ffmpeg:-c:v libx264 -c:a aac", common_options[-1]]

        else:
            command = [*common_options[:-1], "-f", "bestaudio/best", "-x", "--audio-format", AUDIO_EXTENSIONS[extension], "--audio-quality", "0", common_options[-1]]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1)

        playlist_total = None
        playlist_current = 0
        failed_items = []

        for line in process.stdout:
            line = line.strip()

            # Detect which playlist item yt-dlp is currently processing.
            if "Downloading item" in line:
                try:
                    current_part, total_part = line.split("Downloading item", 1)[1].split("of", 1)

                    playlist_current = int(current_part.strip())
                    playlist_total = int(total_part.split()[0].strip())

                    progress_queue.put(("progress", 0, playlist_current, playlist_total))

                except (ValueError, IndexError):
                    pass

            # Download percentage.
            elif "[download]" in line and "%" in line:
                try:
                    progress_percentage = float(line.split("%")[0].split()[-1])

                    if playlist_total and playlist_current:
                        progress_queue.put(("progress", progress_percentage, playlist_current, playlist_total))

                    else:
                        progress_queue.put(("regular_progress", progress_percentage))

                except (ValueError, IndexError):
                    pass

            if "ERROR:" in line:
                failed_items.append(line)

        process.wait()

        if process.returncode == 0:
            progress_queue.put(("complete", folder, failed_items))

        elif playlist_current > 0:
            progress_queue.put(("complete", folder, failed_items))

        else:
            progress_queue.put(("error", "yt-dlp could not start or process the playlist."))

    except FileNotFoundError as error:
        progress_queue.put(("error", f"Could not find required program:\n{error.filename}\n\nMake sure yt-dlp and FFmpeg are installed and available on your PATH."))

    except Exception as error:
        progress_queue.put(("error", str(error)))

def download():
    url = url_entry.get().strip()

    if not url:
        messagebox.showwarning("Missing link", "Please enter a link.")
        return

    if is_playlist(url):
        download_playlist(url)
        return

    download_button.state(["disabled"])
    status_label.config(text="Choose save directory...")

    save_directory = filedialog.askdirectory(title="Choose save directory")

    if not save_directory:
        download_button.state(["!disabled"])
        status_label.config(text="")
        return

    selected_extension = choose_format(root)

    if not selected_extension:
        download_button.state(["!disabled"])
        status_label.config(text="")
        return

    extension = selected_extension.lower()

    if invalid_extension(extension):
        messagebox.showerror("Invalid format", "Please choose a supported format.")
        download_button.state(["!disabled"])
        return

    open_button.state(["disabled"])
    status_label.config(text="Downloading...")
    playlist_progress.config(value=0)
    playlist_progress.grid()

    threading.Thread(target=download_worker, args=(url, save_directory, extension), daemon=True).start()

def download_worker(url: str, save_directory: str, extension: str):
    try:
        yt_dlp = find_executable("yt-dlp")
        ffmpeg = find_executable("ffmpeg")

        output_template = os.path.join(save_directory, "%(title)s.%(ext)s")
        output_path = {"value": None}

        if extension in VIDEO_EXTENSIONS:
            command = [yt_dlp, "--no-playlist", "-f", "bestvideo+bestaudio/best", "--merge-output-format", extension[1:], "--postprocessor-args", "ffmpeg:-c:v libx264 -c:a aac", "--ffmpeg-location", ffmpeg, "-o", output_template, "--print", "after_move:__OUTPUT__:%(filepath)s", url]

        else:
            command = [yt_dlp, "--no-playlist", "-f", "bestaudio/best", "-x", "--audio-format", AUDIO_EXTENSIONS[extension], "--audio-quality", "0", "--ffmpeg-location", ffmpeg, "-o", output_template, "--print", "after_move:__OUTPUT__:%(filepath)s", url]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1)

        for line in process.stdout:
            line = line.strip()

            if line.startswith("__OUTPUT__:"):
                output_path["value"] = line[len("__OUTPUT__:"):].strip()
                continue

            if "[download]" in line and "%" in line:
                try:
                    progress_queue.put(("regular_progress", float(line.split("%")[0].split()[-1])))
                except (ValueError, IndexError):
                    pass

        process.wait()

        if process.returncode == 0:
            final_path = output_path["value"]

            if final_path and os.path.exists(final_path):
                progress_queue.put(("regular_complete", final_path))

            else:
                progress_queue.put(("regular_error", "Download completed, but the downloaded file could not be located."))
        else:
            progress_queue.put(("regular_error", "yt-dlp could not complete the download."))

    except FileNotFoundError as error:
        progress_queue.put(("regular_error", f"Could not find required program:\n{error.filename}\n\nMake sure yt-dlp and FFmpeg are installed and available on your PATH."))

    except Exception as error:
        progress_queue.put(("regular_error", str(error)))

def bulk_url_is_valid(url: str) -> bool:
    url = url.strip()

    if not url:
        return False

    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme.lower() not in ("http", "https"):
        return False

    allowed_domains = {"www.youtube.com", "youtube.com", "m.youtube.com", "youtu.be"}
    domain = parsed.netloc.lower()

    if "@" in domain:
        domain = domain.rsplit("@", 1)[1]

    domain = domain.split(":", 1)[0]

    if domain not in allowed_domains:
        return False

    if is_playlist(url):
        return False

    if domain == "youtu.be":
        return True

    lowered_path = parsed.path.lower()

    if parsed.path == "/" and "watch?v=" in url.lower():
        return True

    if lowered_path.startswith("/watch") and parsed.query:
        if any(parameter.startswith("v=") for parameter in parsed.query.lower().split("&")):
            return True

    if lowered_path.startswith("/shorts/"):
        return True

    return False

def open_bulk_download_window():
    global add_button, delete_button, bulk_window, bulk_progress, bulk_status_label, bulk_download_button

    bulk_window = tk.Toplevel(root)
    bulk_window.title("Bulk Download Videos")
    bulk_window.resizable(False, False)
    bulk_window.transient(root)
    bulk_window.grab_set()

    frame = ttk.Frame(bulk_window, padding=12)
    frame.pack()

    ttk.Label(frame, text="Bulk Download List:").pack(pady=(0, 5))

    listbox = tk.Listbox(frame, width=65, height=10, selectmode=tk.EXTENDED, highlightthickness=0, activestyle="none")
    listbox.pack()

    entry = ttk.Entry(frame, width=65)
    entry.pack(pady=(8, 5))

    def url_already_in_list(url: list[str]) -> bool:
        return url in listbox.get(0, tk.END)

    def add_valid_urls(urls: list[str]) -> int:
        added = 0

        for url in urls:
            url = url.strip()

            if not url:
                continue

            if not bulk_url_is_valid(url):
                continue

            if url_already_in_list(url):
                continue

            listbox.insert(tk.END, url)
            added += 1

        return added

    def update_bulk_buttons(*_: object):
        url = entry.get().strip()

        if bulk_url_is_valid(url):
            add_button.state(["!disabled"])
        else:
            add_button.state(["disabled"])

        if listbox.curselection():
            delete_button.state(["!disabled"])
        else:
            delete_button.state(["disabled"])

        if listbox.size() >= 2:
            bulk_download_button.state(["!disabled"])
        else:
            bulk_download_button.state(["disabled"])

    def add_to_bulk_list():
        url = entry.get().strip()

        if not bulk_url_is_valid(url):
            return

        if url_already_in_list(url):
            entry.delete(0, tk.END)
            update_bulk_buttons()
            return

        listbox.insert(tk.END, url)
        entry.delete(0, tk.END)
        update_bulk_buttons()

    def paste_into_bulk_list(*_: object):
        try:
            pasted_text = bulk_window.clipboard_get()
        except tk.TclError:
            return "break"

        lines = pasted_text.splitlines()

        if len(lines) == 1:
            lines = lines[0].split()

        if add_valid_urls(lines):
            entry.delete(0, tk.END)

        update_bulk_buttons()

        return "break"

    def delete_from_bulk_list():
        selections = listbox.curselection()

        if not selections:
            return

        for index in reversed(selections):
            listbox.delete(index)

        update_bulk_buttons()

    def start_bulk_download():
        if listbox.size() < 2:
            messagebox.showwarning("Not enough videos!", "You must have two or more videos.", parent=bulk_window)
            return

        folder = filedialog.askdirectory(parent=bulk_window, title="Choose bulk download folder")

        if not folder:
            return

        extension = choose_format(bulk_window)

        if not extension:
            return

        bulk_download_button.state(["disabled"])
        add_button.state(["disabled"])
        delete_button.state(["disabled"])

        bulk_status_label.config(text="Starting bulk download...")
        bulk_progress.config(value=0)
        bulk_progress.pack(pady=5)

        threading.Thread(target=bulk_download_worker, args=(list(listbox.get(0, tk.END)), folder, extension), daemon=True).start()

    add_button = ttk.Button(frame, text="Add to Bulk Download List", command=add_to_bulk_list, state="disabled")
    add_button.pack(pady=5)

    delete_button = ttk.Button(frame, text="Delete from Bulk Download List", command=delete_from_bulk_list, state="disabled")
    delete_button.pack(pady=5)

    bulk_download_button = ttk.Button(frame, text="Bulk Download All", command=start_bulk_download, state="disabled")
    bulk_download_button.pack(pady=5)

    bulk_status_label = ttk.Label(frame, text="", justify="center")
    bulk_status_label.pack(pady=(5, 0))

    bulk_progress = ttk.Progressbar(frame, orient="horizontal", length=300, mode="determinate")
    bulk_progress.pack(pady=5)
    bulk_progress.pack_forget()

    entry.bind("<KeyRelease>", update_bulk_buttons)
    entry.bind("<Control-v>", paste_into_bulk_list)
    entry.bind("<Control-V>", paste_into_bulk_list)
    entry.bind("<Command-v>", paste_into_bulk_list)
    entry.bind("<Command-V>", paste_into_bulk_list)
    listbox.bind("<<ListboxSelect>>", update_bulk_buttons)

    def close_bulk_window():
        bulk_window.grab_release()
        bulk_window.destroy()

    bulk_window.protocol("WM_DELETE_WINDOW", close_bulk_window)
    entry.focus_set()

def bulk_download_worker(urls: list[str], folder: str, extension: str):
    try:
        yt_dlp = find_executable("yt-dlp")
        ffmpeg = find_executable("ffmpeg")

        total = len(urls)
        failed_urls = []

        for current, url in enumerate(urls, start=1):
            try:
                if extension in VIDEO_EXTENSIONS:
                    command = [yt_dlp, "--no-playlist", "-f", "bestvideo+bestaudio/best", "--merge-output-format", extension[1:], "--postprocessor-args", "ffmpeg:-c:v libx264 -c:a aac", "--ffmpeg-location", ffmpeg, "-o", os.path.join(folder, "%(title)s.%(ext)s"), url]

                else:
                    command = [yt_dlp, "--no-playlist", "-f", "bestaudio/best", "-x", "--audio-format", AUDIO_EXTENSIONS[extension], "--audio-quality", "0", "--ffmpeg-location", ffmpeg, "-o", os.path.join(folder, "%(title)s.%(ext)s"), url]

                progress_queue.put(("bulk_progress", 0, current, total))
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1)

                for line in process.stdout:
                    line = line.strip()

                    if "[download]" in line and "%" in line:
                        try:
                            progress_queue.put(("bulk_progress", float(line.split("%")[0].split()[-1]), current, total))

                        except (ValueError, IndexError):
                            pass

                process.wait()

                if process.returncode != 0:
                    failed_urls.append(url)
                    progress_queue.put(("bulk_item_error", f"Video {current} of {total} failed.\n\nSkipping and continuing:\n{url}"))

                    continue

            except Exception as error:
                failed_urls.append(url)
                progress_queue.put(("bulk_item_error", f"Video {current} of {total} encountered an error.\n\nSkipping and continuing:\n{url}\n\nError: {error}"))

                continue

        progress_queue.put(("bulk_complete", folder, failed_urls))

    except FileNotFoundError as error:
        progress_queue.put(("bulk_error", f"Could not find required program:\n{error.filename}\n\nMake sure yt-dlp and FFmpeg are installed and available on your PATH."))

    except Exception as error:
        progress_queue.put(("bulk_error", str(error)))

root = tk.Tk()
root.title("yt-dlp Downloader")
root.resizable(False, False)

main_frame = ttk.Frame(root, padding=12)
main_frame.pack()

bulk_button = ttk.Button(main_frame, text="Bulk Download Videos", width=25, command=open_bulk_download_window)
bulk_button.grid(row=0, column=0, columnspan=2, pady=(0, 5))

ttk.Label(main_frame, text="Link:").grid(row=1, column=0, padx=5, pady=5)

url_entry = ttk.Entry(main_frame, width=55)
url_entry.grid(row=1, column=1, pady=5)

download_button = ttk.Button(main_frame, text="Download", width=15, command=download)
download_button.grid(row=2, column=0, columnspan=2, pady=5)

status_label = ttk.Label(main_frame, text="", justify="center")
status_label.grid(row=3, column=0, columnspan=2, pady=5)

playlist_progress = ttk.Progressbar(main_frame, orient="horizontal", length=300, mode="determinate")
playlist_progress.grid(row=4, column=0, columnspan=2, pady=5)
playlist_progress.grid_remove()

open_button = ttk.Button(main_frame, text="Open File", command=open_file, state="disabled")
open_button.grid(row=5, column=0, columnspan=2, pady=5)

url_entry.focus_set()

root.after(50, process_progress_queue)
root.mainloop()