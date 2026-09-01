import os, subprocess, shutil, json
from tkinter import filedialog

extension_dir = filedialog.askdirectory(title="Select VS Code Extension Folder")

if not extension_dir:
    raise SystemExit

def load(*parts):
    return os.path.join(extension_dir, *parts)

extension_js = load("extension.js")
package_json = load("package.json")

if not os.path.isfile(extension_js) or not os.path.isfile(package_json):
    print("The selected folder does not contain extension.js and package.json.")
    raise SystemExit

try:
    vsce_path = shutil.which("vsce")

    if not vsce_path:
        print("Installing vsce...")
        subprocess.run(["npm", "install", "-g", "@vscode/vsce"], check=True)
        vsce_path = shutil.which("vsce")

        if not vsce_path:
            raise FileNotFoundError("vsce could not be found after installation.")

    subprocess.call([vsce_path, "package", "--skip-license", "--allow-missing-repository"], cwd=extension_dir)
    print(f"VSIX built successfully.\n\nOutput folder:\n{extension_dir}")

    with open(package_json, "r") as vsix_file:
        vsix_data = json.load(vsix_file)

    vsix_name = vsix_data.get("name", os.path.basename(extension_dir))
    vsix_ver = vsix_data.get("version", "1.0.0")

    vsix_path = f"{vsix_name}-{vsix_ver}.vsix"
    code_path = shutil.which("code")

    if not code_path:
        raise FileNotFoundError("Cannot find code.")

    subprocess.call([code_path, "--install-extension", vsix_path], cwd=extension_dir)

except subprocess.CalledProcessError as e:
    print(f"Build failed. Error code: {e.returncode}")