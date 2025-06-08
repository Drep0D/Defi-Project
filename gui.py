import tkinter as tk
from tkinter import filedialog, messagebox
from main import procesar_pdf_raw

def seleccionar_pdf():
    ruta = filedialog.askopenfilename(
        title="Selecciona el estado de cuenta",
        filetypes=[("Archivos PDF", "*.pdf")]
    )
    if ruta:
        ruta_pdf.set(ruta)

def procesar_raw():
    ruta = ruta_pdf.get()
    if not ruta:
        messagebox.showwarning("Atención", "Primero selecciona un archivo PDF")
        return
    try:
        procesar_pdf_raw(ruta)
        messagebox.showinfo("Listo", "CSV creado correctamente")
    except Exception as e:
        messagebox.showerror("Error", str(e))

root = tk.Tk()
root.title("Procesar PDF")

ruta_pdf = tk.StringVar()

tk.Button(root, text="Seleccionar PDF", command=seleccionar_pdf).pack(pady=5)
tk.Entry(root, textvariable=ruta_pdf, width=60).pack(pady=5)
tk.Button(root, text="Crear CSV sin modificar", command=procesar_raw).pack(pady=5)

root.mainloop()
