import tkinter as tk
from tkinter import filedialog, messagebox
from main import procesar_pdf_a_csv  # reutilizamos la función existente

def seleccionar_archivo():
    ruta = filedialog.askopenfilename(
        title="Selecciona el estado de cuenta",
        filetypes=[("Archivos PDF", "*.pdf")]
    )
    if ruta:
        ruta_pdf.set(ruta)

def procesar():
    ruta = ruta_pdf.get()
    if not ruta:
        messagebox.showwarning("Atención", "Primero selecciona un archivo PDF.")
        return

    estado.set("Procesando...")
    root.update_idletasks()  # refresca la ventana
    try:
        procesar_pdf_a_csv(ruta)
        estado.set("¡Proceso completado!")
        messagebox.showinfo("Listo", "Se generaron los CSV correctamente.")
    except Exception as e:
        estado.set("Error al procesar")
        messagebox.showerror("Error", str(e))

root = tk.Tk()
root.title("Procesar estado de cuenta")

ruta_pdf = tk.StringVar()
estado = tk.StringVar()

tk.Button(root, text="Seleccionar PDF", command=seleccionar_archivo).pack(pady=5)
tk.Entry(root, textvariable=ruta_pdf, width=50).pack(pady=5)
tk.Button(root, text="Procesar", command=procesar).pack(pady=5)
tk.Label(root, textvariable=estado).pack(pady=5)

root.mainloop()