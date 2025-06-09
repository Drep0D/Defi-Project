import pdfplumber

def leer_pdf(pdf_path):
    """
    Lee un archivo PDF y devuelve una lista de líneas de texto.

    Args:
        pdf_path (str): Ruta al archivo PDF.

    Returns:
        list: Lista de líneas de texto extraídas del PDF.
    """
    lineas = []

    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                # Dividir el texto de la página en líneas
                lineas_pagina = texto.split('\n')
                # Añadir las líneas de esta página a la lista general
                lineas.extend(lineas_pagina)

    return lineas