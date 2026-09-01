import ast, tkinter as tk
from tkinter import ttk, filedialog

class ModuleUseFinder:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Module Use Finder")
        self.root.withdraw()
        self.root.resizable(False, False)

        self.module_uses: dict[str, set[str]] = {}
        self.modules: list[str] = []
        self.imported_modules: set[str] = set()

        self._build_ui()
        self._load_files_on_boot()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Select module:").pack(anchor="w")

        self.module_var = tk.StringVar()
        self.module_dropdown = ttk.Combobox(frame, textvariable=self.module_var, state="readonly")
        self.module_dropdown.pack(fill="x", pady=6)

        ttk.Button(frame, text="Get Module Uses", command=self.copy_module_uses).pack(pady=10)
        ttk.Button(frame, text="Get All Used Modules", command=self.copy_all_used_modules).pack(pady=10)

    def _load_files_on_boot(self):
        paths = filedialog.askopenfilenames(title="Select Python scripts", filetypes=[("Python files", "*.py")])

        if not paths:
            self.root.destroy()
            return

        self.root.deiconify()

        for path in paths:
            self._scan_file(path)

        self.modules = sorted(self.imported_modules)
        self.module_dropdown["values"] = self.modules

        if self.modules:
            self.module_dropdown.current(0)

    def _scan_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except Exception:
            return

        imported_modules = self._collect_imports(tree)
        self.imported_modules.update(imported_modules.values())

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                full_name = self._get_attribute_chain(node)
                if not full_name:
                    continue

                root = full_name.split(".", 1)[0]

                if root in imported_modules:
                    real_module = imported_modules[root]
                    uses = self.module_uses.setdefault(real_module, set())
                    uses.add(full_name.replace(root, real_module, 1))

    def _collect_imports(self, tree: ast.AST) -> dict[str, str]:
        """
        Returns mapping:
        alias -> real module
        """
        imports: dict[str, str] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for item in node.names:
                    name = item.name
                    imports[item.asname or name.split(".", 1)[0]] = name.split(".", 1)[0]

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".", 1)[0]

                    for item in node.names:
                        imports[item.asname or item.name] = root

        return imports

    def _get_attribute_chain(self, node: ast.Name) -> str | None:
        parts = []

        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value

        if isinstance(node, ast.Name):
            parts.append(node.id)
            return ".".join(reversed(parts))

        return None

    def copy_module_uses(self):
        module = self.module_var.get()

        if not module:
            return

        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(sorted(self.module_uses.get(module, []))))
        self.root.update()

    def copy_all_used_modules(self):
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(str(module) for module in self.modules))
        self.root.update()

root = tk.Tk()
ModuleUseFinder(root)
root.mainloop()
