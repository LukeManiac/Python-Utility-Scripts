import os, shutil, tempfile, win32com.client
from tkinter import filedialog

def convert_to_temp_pdf(word_app: win32com.client.CDispatch, source_file: str, temp_dir: str) -> str:
    print(f"Imported {source_file.replace("/", "\\")}")
    temp_pdf = os.path.join(temp_dir, f"{os.path.splitext(os.path.basename(source_file))[0]}.pdf")
    doc = word_app.Documents.Open(os.path.abspath(source_file))

    try:
        doc.ExportAsFixedFormat(OutputFileName=os.path.abspath(temp_pdf), ExportFormat=17)
    finally:
        doc.Close(False)

    return temp_pdf

input_files = list(filedialog.askopenfilenames(title="Select Word Document(s)", filetypes=[("Word Documents", "*.doc *.docx *.docm *.dot *.dotx *.dotm")]))

if not input_files:
    raise SystemExit

print(f"Imported total files: {len(input_files)}")

word = win32com.client.Dispatch("Word.Application")
word.Visible = False

try:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_outputs = [(file, convert_to_temp_pdf(word, file, temp_dir)) for file in input_files]

        if len(temp_outputs) == 1:
            source, temp_pdf = temp_outputs[0]
            output_file = filedialog.asksaveasfilename(title="Save PDF As", initialdir=os.path.dirname(source), initialfile=os.path.splitext(os.path.basename(source))[0] + ".pdf", defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])

            if not output_file:
                raise SystemExit

            shutil.move(temp_pdf, output_file)
            print(f"Exported {output_file}")
        else:
            output_dir = filedialog.askdirectory(title="Select Folder to Save PDFs")

            if not output_dir:
                raise SystemExit

            for source, temp_pdf in temp_outputs:
                save_path = os.path.join(output_dir, os.path.splitext(os.path.basename(source))[0] + ".pdf")
                shutil.move(temp_pdf, save_path)
                print(f"Exported {save_path}")

finally:
    word.Quit()

print("Conversion complete.")