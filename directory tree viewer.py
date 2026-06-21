import os, tkinter as tk
from tkinter import filedialog, ttk

bg = "black"
fg = "white"

shift_pressed = False

def shift_check(event: tk.Event):
    global shift_pressed
    shift_pressed = bool(event.state & 0x0001)

def populate_tree(parent, path):
    """Add folders first, then files to the tree."""
    try:
        entries = sorted(os.listdir(path), key=str.lower)

        # Insert folders first
        for entry in [entry for entry in entries if os.path.isdir(os.path.join(path, entry))]:
            tree.insert(tree.insert(parent, 'end', text=entry, open=False, values=[os.path.join(path, entry)]), 'end', text="Loading...")  # Dummy for expandable folder

        # Then insert files
        for entry in [entry for entry in entries if os.path.isfile(os.path.join(path, entry))]:
            tree.insert(parent, 'end', text=entry, values=[os.path.join(path, entry)])

    except PermissionError:
        pass  # Skip folders we can't access

def on_open(event):
    """Load folder contents when a node is expanded."""
    selected_item = tree.focus()
    children = tree.get_children(selected_item)

    if children and tree.item(children[0], 'text') == "Loading...":
        tree.delete(children[0])
        populate_tree(selected_item, tree.item(selected_item, 'values')[0])

def choose_directory():
    directory = filedialog.askdirectory()

    if directory:
        tree.delete(*tree.get_children())
        populate_tree('', directory)   # ← no visible root node
        activify(copy_btn, expand_btn, collapse_btn)

def on_double_click(event):
    """Open folder in explorer or show Open With for files."""
    path = tree.item(tree.focus(), 'values')[0]

    if os.path.isfile(path):
        os.startfile(path)

def build_filesystem_structure(path, prefix="", is_root=True, copy_ext=True) -> str:
    """Build folder/file structure where root level has no connectors."""
    text = ""

    try:
        entries = sorted(os.listdir(path), key=str.lower)
        folders = [entry for entry in entries if os.path.isdir(os.path.join(path, entry))]
        files = [entry for entry in entries if os.path.isfile(os.path.join(path, entry))]

        # ROOT LEVEL — no tree symbols
        if is_root:
            for folder in folders:
                text += f"{folder}\n"
                text += build_filesystem_structure(os.path.join(path, folder), "", False, copy_ext)

            for file in files:
                text += f"{file if copy_ext else os.path.splitext(file)[0]}\n"

            return text

        # NESTED LEVELS — use tree symbols
        for i, folder in enumerate(folders):
            connector = "└── " if i == len(folders) - 1 and not files else "├── "
            text += f"{prefix}{connector}{folder}\n"
            text += build_filesystem_structure(os.path.join(path, folder), prefix + "    " if connector == "└── " and not files else "│   ", False, copy_ext)

        for i, file in enumerate(files):
            text += f"{prefix}{"└── " if i == len(files) - 1 else "├── "}{file if copy_ext else os.path.splitext(file)[0]}\n"

    except PermissionError:
        pass

    return text

def copy_as_file_structure():
    selected_nodes = tree.get_children('')

    if not selected_nodes:
        return

    selected_node = selected_nodes[0]
    item_values = tree.item(selected_node, 'values')
    full_path = item_values[0]
    directory = os.path.dirname(full_path)
    filesystem_structure = build_filesystem_structure(directory, copy_ext=shift_pressed)
    result = filesystem_structure.rstrip()

    root.clipboard_clear()
    root.clipboard_append(result)
    root.update()

def on_right_arrow(event):
    """Expand the selected folder in the Treeview."""
    selected_item = tree.focus()

    if not selected_item:
        return

    # Only toggle open if it has children
    if tree.get_children(selected_item):
        if not tree.item(selected_item, "open"):
            tree.item(selected_item, open=True)
            # Load children if folder was just opened
            on_open(event)

def on_left_arrow(event):
    """Collapse the selected folder in the Treeview."""
    selected_item = tree.focus()

    if not selected_item:
        return

    if tree.get_children(selected_item):
        if tree.item(selected_item, "open"):
            tree.item(selected_item, open=False)

def on_return(event):
    """Open the selected folder in Explorer only."""
    selected_item = tree.focus()

    if not selected_item:
        return "break"  # Stop further handling

    os.startfile(tree.item(selected_item, "values")[0])
    return "break"  # Prevent Treeview from expanding

def expand_all():
    """Recursively expand every folder in the tree."""
    def recurse(item):
        children = tree.get_children(item)

        if children:
            # Open this node
            tree.item(item, open=True)
            # Load folder contents if it's a dummy

            if children and tree.item(children[0], 'text') == "Loading...":
                tree.delete(children[0])
                populate_tree(item, tree.item(item, 'values')[0])

            for child in children:
                recurse(child)

    for root_item in tree.get_children(''):
        recurse(root_item)

def collapse_all():
    """Recursively collapse every folder in the tree."""
    def recurse(item):
        for child in tree.get_children(item):
            recurse(child)

        tree.item(item, open=False)

    for root_item in tree.get_children(''):
        recurse(root_item)

def create_button(text, command, disabled=False) -> ttk.Button:
    button = ttk.Button(button_frame, text=text, command=command, style="Console.TButton")

    if disabled:
        button.state(["disabled"])

    return button

def activify(*buttons):
    for button in buttons:
        button: ttk.Button
        button.state(["!disabled"])

# Main window
root = tk.Tk()
root.title("Console File Explorer")
root.geometry("900x600")
root.configure(bg=bg)
root.bind("<KeyPress>", shift_check)
root.bind("<KeyRelease>", shift_check)

# Frame for buttons
button_frame = tk.Frame(root, bg=bg)
button_frame.pack(pady=10)

choose_btn = create_button("Select Directory", choose_directory)
choose_btn.pack(side=tk.LEFT, padx=5)

copy_btn = create_button("Copy as File Structure", copy_as_file_structure, True)
copy_btn.pack(side=tk.LEFT, padx=5)

expand_btn = create_button("Expand All", expand_all, True)
expand_btn.pack(side=tk.LEFT, padx=5)

collapse_btn = create_button("Collapse All", collapse_all, True)
collapse_btn.pack(side=tk.LEFT, padx=5)

# Frame for treeview and scrollbar
frame = tk.Frame(root, bg=bg)
frame.pack(fill=tk.BOTH, expand=True)

# Scrollbar styling
style = ttk.Style()
style.theme_use('clam')
style.configure("Console.Treeview", background=bg, foreground=fg, fieldbackground=bg)
style.configure("Console.TButton", background=bg, foreground=fg, padding=5)
style.map("Console.Treeview", background=[("selected", fg)], foreground=[("selected", bg)])
style.map("Console.TButton", background=[("disabled", "#222222"), ("pressed", "#444444"), ("active", "#333333")], foreground=[("disabled", "#777777")])

tree_scroll = ttk.Scrollbar(frame)
tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

# Treeview
tree = ttk.Treeview(frame, yscrollcommand=tree_scroll.set, style="Console.Treeview")
tree.pack(fill=tk.BOTH, expand=True)
tree.focus_set()
tree_scroll.config(command=tree.yview)

# Bind expanding folders and double-click
tree.bind('<<TreeviewOpen>>', on_open)
tree.bind("<Double-1>", on_double_click)
tree.bind("<Right>", on_right_arrow)
tree.bind("<Left>", on_left_arrow)
tree.bind("<Return>", on_return)

root.mainloop()