import shutil, subprocess, tempfile, os, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from mutagen import File
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TPE2, TCOM, TCON, TYER, TBPM, TXXX, COMM, USLT, ID3NoHeaderError
from mutagen.wave import WAVE
from PIL import Image

METADATA_ELEMENTS = [
    "Title",
    "Artist",
    "Album",
    "Album Artist",
    "Composer",
    "Grouping",
    "Genre",
    "Date",
    "BPM",
    "Keywords",
    "Comments",
    "Lyrics",
    "Artwork",
]

EASY_KEYS = {element: element.lower().replace(" ", "") for element in METADATA_ELEMENTS}

class MetadataEditorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Metadata Editor")
        self.geometry("850x650")
        self.resizable(True, True)

        self.source_path = None
        self.artwork_path = None
        self._audio_tags = {}
        self.vars = {el: tk.StringVar() for el in METADATA_ELEMENTS if el not in ("Comments", "Lyrics", "Artwork")}
        self._build_ui()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        top_row = ttk.Frame(frm)
        top_row.pack(fill=tk.X, anchor="nw", pady=(0,8))
        self.import_btn = ttk.Button(top_row, text="Import Audio File", command=self.import_audio)
        self.import_btn.pack(side=tk.LEFT)

        self.import_meta_btn = ttk.Button(top_row, text="Import Metadata from MP3", command=self.import_metadata_from_file, state=tk.DISABLED)
        self.import_meta_btn.pack(side=tk.LEFT, padx=6)

        self.export_btn = ttk.Button(top_row, text="Export MP3", command=self.export_mp3, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=6)

        self.clear_meta_btn = ttk.Button(top_row, text="Clear Metadata", command=self.clear_metadata, state=tk.DISABLED)
        self.clear_meta_btn.pack(side=tk.LEFT, padx=6)

        self.reset_btn = ttk.Button(top_row, text="Reset Data", command=self.reset_app, state=tk.DISABLED)
        self.reset_btn.pack(side=tk.LEFT)

        content = ttk.Frame(frm)
        content.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(content)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right = ttk.Frame(content)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        def labelled_entry(parent, label_text, var=None, widget: tk.Widget=None):
            row = ttk.Frame(parent)
            row.pack(fill=tk.X, pady=4)
            lbl = ttk.Label(row, text=label_text, width=20, anchor='w')
            lbl.pack(side=tk.LEFT)

            if widget:
                widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
            else:
                ent = ttk.Entry(row, textvariable=var)
                ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
                return ent

            return None

        self.title_entry = labelled_entry(left, "Title:", var=self.vars["Title"])
        self.artist_entry = labelled_entry(left, "Artist:", var=self.vars["Artist"])
        self.album_entry = labelled_entry(left, "Album:", var=self.vars["Album"])
        self.album_artist_entry = labelled_entry(left, "Album Artist:", var=self.vars["Album Artist"])
        self.composer_entry = labelled_entry(left, "Composer:", var=self.vars["Composer"])
        self.grouping_entry = labelled_entry(left, "Grouping:", var=self.vars["Grouping"])
        self.genre_entry = labelled_entry(left, "Genre:", var=self.vars["Genre"])

        date_row = ttk.Frame(left)
        date_row.pack(fill=tk.X, pady=4)
        ttk.Label(date_row, text="Date:", width=20, anchor='w').pack(side=tk.LEFT)
        date_spin = ttk.Spinbox(date_row, from_=0, to=9999, textvariable=self.vars["Date"], width=10, state="readonly")
        date_spin.pack(side=tk.LEFT, fill=tk.X, expand=True)

        bpm_row = ttk.Frame(left)
        bpm_row.pack(fill=tk.X, pady=4)
        ttk.Label(bpm_row, text="BPM:", width=20, anchor='w').pack(side=tk.LEFT)
        bpm_spin = ttk.Spinbox(bpm_row, from_=0.0, to=9999.9, increment=0.1, textvariable=self.vars["BPM"], width=10, state="readonly")
        bpm_spin.pack(side=tk.LEFT, fill=tk.X, expand=True)

        date_spin['justify'] = 'left'
        bpm_spin['justify'] = 'left'

        self.keywords_entry = labelled_entry(left, "Keywords\n(comma-separated):", var=self.vars["Keywords"])

        art_row = ttk.Frame(left)
        art_row.pack(fill=tk.X, pady=6)
        art_lbl = ttk.Label(art_row, text="Artwork:", width=20, anchor='w')
        art_lbl.pack(side=tk.LEFT)
        self.artwork_label = ttk.Label(art_row, text="(none)", anchor='w')
        self.artwork_label.pack(side=tk.LEFT, padx=(0,6), fill=tk.X, expand=True)
        self.import_art_btn = ttk.Button(art_row, text="Import Artwork", command=self.import_artwork)
        self.import_art_btn.pack(side=tk.LEFT)

        comments_box_lbl = ttk.Label(right, text="Comments", anchor='w')
        comments_box_lbl.pack(anchor='nw')
        self.comments_text = tk.Text(right, height=8, wrap=tk.WORD)
        comments_scroll = ttk.Scrollbar(right, command=self.comments_text.yview)
        self.comments_text['yscrollcommand'] = comments_scroll.set
        self.comments_text.pack(fill=tk.BOTH, expand=False)
        comments_scroll.pack(fill=tk.Y, side=tk.RIGHT)

        lyrics_box_lbl = ttk.Label(right, text="Lyrics", anchor='w')
        lyrics_box_lbl.pack(anchor='nw', pady=(8,0))
        self.lyrics_text = tk.Text(right, height=12, wrap=tk.WORD)
        lyrics_scroll = ttk.Scrollbar(right, command=self.lyrics_text.yview)
        self.lyrics_text['yscrollcommand'] = lyrics_scroll.set
        self.lyrics_text.pack(fill=tk.BOTH, expand=True)
        lyrics_scroll.pack(fill=tk.Y, side=tk.RIGHT)

    def clear_metadata(self):
        self._audio_tags = {}
        for var in self.vars.values():
            var.set("")

        audio: WAVE = File(self.source_path, easy=False)

        if audio.tags is not None:
            audio.tags.clear()
            audio.save()

        self.comments_text.delete("1.0", tk.END)
        self.lyrics_text.delete("1.0", tk.END)

        self.artwork_path = None
        self.artwork_label.config(text="(none)")

        self.export_btn.config(state=tk.NORMAL)
        self.reset_btn.config(state=tk.NORMAL)

    def reset_app(self):
        self.source_path = None
        self.artwork_path = None
        self._audio_tags = {}

        for var in self.vars.values():
            var.set("")

        self.comments_text.delete("1.0", tk.END)
        self.lyrics_text.delete("1.0", tk.END)

        self.artwork_label.config(text="(none)")

        self.export_btn.config(state=tk.DISABLED)
        self.import_meta_btn.config(state=tk.DISABLED)
        self.clear_meta_btn.config(state=tk.DISABLED)
        self.reset_btn.config(state=tk.DISABLED)

        self.import_btn.focus_set()

    def import_audio(self):
        path = filedialog.askopenfilename(title="Select audio file", filetypes=[("Audio files", "*.mp3 *.wav *.ogg"), ("All files", "*.*")])

        if not path:
            return

        self.source_path = path
        self.import_meta_btn.config(state=tk.NORMAL)
        self.reset_btn.config(state=tk.NORMAL)
        self.clear_meta_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.NORMAL)
        self._load_tags(path)
        self._populate_fields_from_loaded_tags()

    def _load_tags(self, path: str):
        self._audio_tags = {}
        audio = File(path, easy=False)
        easy: dict = File(path, easy=True)

        if easy:
            for human, key in EASY_KEYS.items():
                val = None

                if key in easy:
                    v = easy.get(key)
                    if isinstance(v, (list, tuple)):
                        val = ", ".join(v)
                    else:
                        val = str(v)

                if val:
                    self._audio_tags[human] = val

        if path.lower().endswith(".mp3"):
            try:
                id3 = ID3(path)

                tag_map = {
                    "TIT2": "Title",
                    "TPE1": "Artist",
                    "TALB": "Album",
                    "TPE2": "Album Artist",
                    "TCOM": "Composer",
                    "TCON": "Genre",
                    "TYER": "Date",
                    "TBPM": "BPM",
                }

                for key, label in tag_map.items():
                    if key in id3:
                        self._audio_tags.setdefault(label, str(id3.get(key)))

                comms = id3.getall("COMM")

                if comms:
                    self._audio_tags["Comments"] = comms[0].text[0] if comms[0].text else ""

                uslt = id3.getall("USLT")

                if uslt:
                    self._audio_tags["Lyrics"] = uslt[0].text if uslt[0].text else ""

                apics = id3.getall("APIC")

                if apics:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    tmp.write(apics[0].data)
                    tmp.flush()
                    tmp.close()
                    self._audio_tags["Artwork"] = tmp.name
            except ID3NoHeaderError:
                pass
        else:
            if audio:
                try:
                    if hasattr(audio, "tags") and audio.tags:
                        for key in audio.tags.keys():
                            tag_map = {
                                "comment": ("Comments", "; "),
                                "lyrics": ("Lyrics", "; "),
                                "bpm": ("BPM", ", "),
                                "date": ("Date", ", "),
                                "title": ("Title", ", "),
                                "artist": ("Artist", ", "),
                                "album": ("Album", ", "),
                                "albumartist": ("Album Artist", ", "),
                                "composer": ("Composer", ", "),
                                "genre": ("Genre", ", "),
                                "keywords": ("Keywords", ", "),
                            }

                            for key in audio.tags:
                                low = key.lower()

                                for match, (label, sep) in tag_map.items():
                                    if match in low and label not in self._audio_tags:
                                        self._audio_tags[label] = sep.join(audio.tags.get(key))
                except Exception:
                    pass

                pics = []

                if hasattr(audio, "pictures"):
                    pics = audio.pictures

                if audio.tags:
                    for k, v in audio.tags.items():
                        if "metadata_block_picture" in k.lower() or "picture" in k.lower():
                            pass

                if pics:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    tmp.write(pics[0].data)
                    tmp.flush()
                    tmp.close()
                    self._audio_tags["Artwork"] = tmp.name

    def _populate_fields_from_loaded_tags(self):
        for _, var in self.vars.items():
            var.set("")

        self.comments_text.delete("1.0", tk.END)
        self.lyrics_text.delete("1.0", tk.END)
        self.artwork_path = None
        self.artwork_label.config(text="(none)")

        for el in METADATA_ELEMENTS:
            if el == "Comments":
                if "Comments" in self._audio_tags:
                    self.comments_text.insert("1.0", self._audio_tags.get("Comments", ""))

            elif el == "Lyrics":
                if "Lyrics" in self._audio_tags:
                    self.lyrics_text.insert("1.0", self._audio_tags.get("Lyrics", ""))

            elif el == "Artwork":
                if "Artwork" in self._audio_tags:
                    self.artwork_path = self._audio_tags.get("Artwork")
                    self.artwork_label.config(text=os.path.basename(self.artwork_path))

            else:
                if el in self._audio_tags:
                    self.vars[el].set(self._audio_tags[el])

    def import_artwork(self):
        p = filedialog.askopenfilename(title="Import Artwork", filetypes=[("Images", "*.png *.png *.jpeg *.bmp *.webp"), ("All files", "*.*")])

        if not p:
            return

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        img = Image.open(p).convert("RGBA")
        img.save(tmp.name, format="PNG")
        tmp.close()
        self.artwork_path = tmp.name
        self.artwork_label.config(text=os.path.basename(tmp.name))

    def import_metadata_from_file(self):
        p = filedialog.askopenfilename(title="Select audio file to import metadata from", filetypes=[("Audio files", "*.mp3 *.wav *.ogg"), ("All files", "*.*")])

        if not p:
            return

        other = File(p, easy=False)

        if not other:
            messagebox.showwarning("Unsupported", "Couldn't read tags from selected file.")
            return

        temp_tags = {}
        audio = File(p, easy=True)

        if audio:
            for human, key in EASY_KEYS.items():
                if key in audio:
                    v = audio.get(key)
                    if isinstance(v, (list, tuple)):
                        temp_tags[human] = ", ".join(v)
                    else:
                        temp_tags[human] = str(v)

        if p.lower().endswith(".mp3"):
            try:
                id3 = ID3(p)

                if id3.getall("APIC"):
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    tmp.write(id3.getall("APIC")[0].data)
                    tmp.flush(); tmp.close()
                    temp_tags["Artwork"] = tmp.name

                comms = id3.getall("COMM")

                if comms:
                    comm: COMM = comms[0]
                    temp_tags["Comments"] = comm.text[0] if comm.text else ""

                uslt = id3.getall("USLT")

                if uslt:
                    uslt_obj: USLT = uslt[0]
                    temp_tags["Lyrics"] = uslt_obj.text if uslt_obj.text else ""

            except Exception:
                pass

        else:
            if hasattr(other, "tags") and other.tags:
                t = other.tags

                for k in t.keys():
                    low = k.lower()
                    tag_map = {
                        "title": "Title",
                        "artist": "Artist",
                        "album": "Album",
                        "albumartist": "Album Artist",
                        "composer": "Composer",
                        "genre": "Genre",
                        "date": "Date",
                        "bpm": "BPM",
                        "comment": "Comments",
                        "lyrics": "Lyrics",
                    }

                    for k in t:
                        low = k.lower()

                        for match, label in tag_map.items():
                            if match in low:
                                temp_tags.setdefault(label, ", ".join(t.get(k)))

                if hasattr(other, "pictures") and other.pictures:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    tmp.write(other.pictures[0].data)
                    tmp.flush(); tmp.close()
                    temp_tags["Artwork"] = tmp.name

        available = [el for el in METADATA_ELEMENTS if el in temp_tags]

        if not available:
            messagebox.showinfo("No metadata", "No recognised metadata found in that file.")
            return

        dlg = tk.Toplevel(self)
        dlg.title("Metadata elements to import")
        dlg.geometry("420x400")
        dlg.transient(self)
        frame = ttk.Frame(dlg, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Select metadata elements to import:", anchor='w').pack(anchor='w', pady=(0,6))
        checks = {}
        chk_container = ttk.Frame(frame)
        chk_container.pack(fill=tk.BOTH, expand=True)

        for el in available:
            v = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(chk_container, text=el, variable=v)
            chk.pack(anchor='w', pady=2)
            checks[el] = v

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=8)

        def do_import():
            for el, var in checks.items():
                if var.get():
                    val = temp_tags.get(el, "")

                    if el == "Artwork":
                        self.artwork_path = val
                        self.artwork_label.config(text=os.path.basename(val))
                    elif el == "Comments":
                        self.comments_text.delete("1.0", tk.END)
                        self.comments_text.insert("1.0", val)
                    elif el == "Lyrics":
                        self.lyrics_text.delete("1.0", tk.END)
                        self.lyrics_text.insert("1.0", val)
                    else:
                        if el in self.vars:
                            self.vars[el].set(val)

            dlg.destroy()

        ttk.Button(btn_row, text="Import selected", command=do_import).pack(side=tk.RIGHT)
        ttk.Button(btn_row, text="Cancel", command=dlg.destroy).pack(side=tk.RIGHT, padx=(0,6))

        dlg.wait_window()

    def export_mp3(self):
        if not self.source_path:
            messagebox.showwarning("No source", "Please import an audio file first.")
            return

        dest = filedialog.asksaveasfilename(title="Export MP3", defaultextension=".mp3", filetypes=[("MP3 files", "*.mp3")])

        if not dest:
            return

        metadata = {}

        for el in METADATA_ELEMENTS:
            if el == "Comments":
                metadata["Comments"] = self.comments_text.get("1.0", tk.END).strip()
            elif el == "Lyrics":
                metadata["Lyrics"] = self.lyrics_text.get("1.0", tk.END).strip()
            elif el == "Artwork":
                metadata["Artwork"] = self.artwork_path
            else:
                if el in self.vars:
                    metadata[el] = self.vars[el].get().strip()

        try:
            if self.source_path.lower().endswith(".mp3"):
                shutil.copy2(self.source_path, dest)
                self._write_mp3_tags(dest, metadata)
                messagebox.showinfo("Exported", f"Exported MP3 and updated metadata: {dest}")
            else:
                if shutil.which("ffmpeg") is None:
                    messagebox.showwarning("FFmpeg required", "Source is not MP3. To export MP3 without losing control over encoding, ffmpeg must be installed and in PATH.\n\nInstall ffmpeg or export from an MP3 source to preserve quality.")
                    return

                tmp_out = dest + ".tmp.mp3"
                subprocess.check_call(["ffmpeg", "-y", "-i", self.source_path, "-codec:a", "libmp3lame", "-qscale:a", "2", tmp_out])
                self._write_mp3_tags(tmp_out, metadata)
                shutil.move(tmp_out, dest)
                messagebox.showinfo("Exported", f"Exported MP3: {dest}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export MP3: {e}")

    def _write_mp3_tags(self, mp3_path, metadata: dict):
        try:
            try:
                id3 = ID3(mp3_path)
            except ID3NoHeaderError:
                id3 = ID3()

            frame_map = {
                "Title": TIT2,
                "Artist": TPE1,
                "Album": TALB,
                "Album Artist": TPE2,
                "Composer": TCOM,
                "Genre": TCON,
                "Date": TYER,
                "BPM": TBPM,
            }

            for key, frame in frame_map.items():
                if metadata.get(key):
                    value = metadata[key]

                    if key == "BPM":
                        value = str(value)

                    id3.add(frame(encoding=3, text=value))

            text_map = {
                "Comments": COMM,
                "Lyrics": USLT,
                "Keywords": TXXX
            }

            for key, frame in text_map.items():
                if metadata.get(key):
                    value = metadata[key]
                    id3.add(frame(encoding=3, lang="eng", desc="", text=metadata[key]))

            art_path: str = metadata.get("Artwork")

            if art_path and os.path.exists(art_path):
                with open(art_path, "rb") as f:
                    data = f.read()

                ext = os.path.splitext(art_path)[1].lower()
                mime = "image/png"

                img_map = ["png", "jpeg", "jpg", "bmp", "webp"]

                for ext in img_map:
                    if art_path.lower().endswith(f".{ext}"):
                        mime = f"image/{ext}"
                        break

                id3.delall("APIC")
                id3.add(APIC(encoding=3, mime=mime, type=3, desc='Cover', data=data))

            id3.save(mp3_path)

        except:
            raise

app = MetadataEditorApp()
app.mainloop()