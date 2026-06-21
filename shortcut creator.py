import os, sys, win32com.client, subprocess, tkinter as tk
from tkinter import filedialog, messagebox, ttk

class ShortcutCreatorApp:
    def __init__(self, root: tk.Tk, initial_path=None):
        self.root = root
        self.root.title("Shortcut Creator")
        self.root.resizable(False, False)

        self.file_path = tk.StringVar()
        self.comment = tk.StringVar()
        self.icon_path = tk.StringVar()
        self.run_option = tk.StringVar(value="Normal")

        ttk.Label(self.root, text="File to Run").pack(pady=(10, 0))
        self.path_entry = ttk.Entry(self.root, textvariable=self.file_path, width=50, justify='center')
        self.path_entry.pack(pady=5)

        frame_buttons = ttk.Frame(self.root)
        frame_buttons.pack(pady=5)
        ttk.Button(frame_buttons, text="Replace File Path", command=self.select_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_buttons, text="Replace Folder Path", command=self.select_folder).pack(side=tk.LEFT, padx=5)

        ttk.Label(self.root, text="Run").pack(pady=(10, 0))
        self.run_dropdown = ttk.Combobox(self.root, values=["Normal", "Minimized", "Maximized"], state="readonly", textvariable=self.run_option)
        self.run_dropdown.pack(pady=5)

        ttk.Label(self.root, text="Comment").pack(pady=(10, 0))
        ttk.Entry(self.root, textvariable=self.comment, width=50, justify='center').pack(pady=5)

        set_icon_frame = ttk.Frame(self.root)
        set_icon_frame.pack(pady=(0, 10))
        ttk.Button(set_icon_frame, text="Set Icon", command=self.set_icon).pack(side=tk.LEFT, padx=5)

        frame_action = ttk.Frame(self.root)
        frame_action.pack(pady=10)
        ttk.Button(frame_action, text="Open File Location", command=self.open_location).pack(side=tk.LEFT, padx=10)
        self.create_btn = ttk.Button(frame_action, text="Create Shortcut", command=self.create_shortcut, state=tk.DISABLED)
        self.create_btn.pack(side=tk.LEFT, padx=10)

        self.file_path.trace_add("write", self.validate_path)

        if initial_path and os.path.exists(initial_path):
            self.file_path.set(initial_path)
            self.icon_path.set(initial_path)

        self.root.update_idletasks()
        self.root.geometry(f"{self.root.winfo_width() + 20}x{self.root.winfo_height()}")

    def select_file(self):
        path = filedialog.askopenfilename()

        if path:
            self.file_path.set(path)
            self.icon_path.set(path)

    def select_folder(self):
        path = filedialog.askdirectory()

        if path:
            self.file_path.set(path)
            self.icon_path.set("%SystemRoot%\\System32\\shell32.dll,3")

    def validate_path(self, *args):
        state = tk.NORMAL if os.path.exists(self.file_path.get()) else tk.DISABLED
        self.create_btn.config(state=state)

    def open_location(self):
        path = self.file_path.get()

        if os.path.exists(path):
            subprocess.Popen(f'explorer "{os.path.dirname(path) if os.path.isfile(path) else path}"')
        else:
            messagebox.showerror("Error", "Written path does not exist. Please select another file/folder.")

    def set_icon(self):
        filetypes = [("Image/Icon files", "*.ico;*.png;*.bmp;*.gif"), ("ICO files", "*.ico"), ("PNG files", "*.png"), ("BMP files", "*.bmp"), ("GIF files", "*.gif"), ("All files", "*.*")]
        icon_path = filedialog.askopenfilename(title="Select Icon File", filetypes=filetypes)

        if icon_path:
            self.icon_path.set(icon_path)

    def create_shortcut(self):
        path = self.file_path.get()

        if not os.path.exists(path):
            messagebox.showerror("Error", "Written path does not exist. Please select another file/folder.")
            return

        if os.path.isdir(path):
            default_name = os.path.basename(os.path.normpath(path)) + ".lnk"
        else:
            default_name = os.path.splitext(os.path.basename(path))[0] + ".lnk"

        shortcut_path = filedialog.asksaveasfilename(defaultextension=".lnk", filetypes=[("Shortcut", "*.lnk")], title="Save Shortcut As", initialfile=default_name)

        if not shortcut_path:
            return

        shell: win32com.client.CDispatch = win32com.client.Dispatch("WScript.Shell")
        shortcut: win32com.client.CDispatch = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = path
        shortcut.WorkingDirectory = os.path.dirname(path)
        shortcut.WindowStyle = {"Normal": 1, "Minimized": 7, "Maximized": 3}[self.run_option.get()]
        shortcut.Description = self.comment.get()
        shortcut.IconLocation = self.icon_path.get()
        shortcut.save()

        messagebox.showinfo("Success", f"Shortcut created at:\n{shortcut_path}")

passed_path = sys.argv[1] if len(sys.argv) > 1 else None
root = tk.Tk()
app = ShortcutCreatorApp(root, initial_path=passed_path)
root.mainloop()
