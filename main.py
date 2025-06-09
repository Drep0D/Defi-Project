import json
import pdfplumber
import pandas as pd
from model.processor import TransactionProcessor
from reader import leer_pdf

def load_config(path: str = "config.json") -> dict:
    """Carga el archivo de configuración JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def procesar_pdf_raw(pdf_path: str, output: str = "transacciones_raw.csv"):
    """Genera un CSV con las transacciones tal como aparecen en el estado de cuenta."""
    transacciones = []
    lineas = leer_pdf(pdf_path)

    for linea in lineas:
        if es_linea_transaccion(linea):
            t = extraer_transaccion_raw(linea)
            if t:
                transacciones.append(t)

    if transacciones:
        pd.DataFrame(transacciones).to_csv(output, index=False)
        print(f"✅ CSV sin procesar guardado en {output}")


def procesar_pdf_a_csv(pdf_path: str, config: dict):
    """Procesa un extracto bancario PDF y genera archivos CSV con las transacciones."""
    processor = TransactionProcessor(config.get("common_companies"))
    transacciones = []
    lineas = leer_pdf(pdf_path)

    for linea in lineas:
        if es_linea_transaccion(linea):
            t = extraer_transaccion(linea, processor, config)
            if t:
                transacciones.append(t)
    guardar_transacciones(transacciones, config["outputs"])


def es_linea_transaccion(linea: str) -> bool:
    """Determina si una línea contiene una transacción bancaria."""
    return ('/' in linea
            and any(char.isdigit() for char in linea)
            and len(linea.split()) >= 3)


def extraer_transaccion_raw(linea: str) -> dict | None:
    """Devuelve la información de la transacción sin limpiar la descripción."""
    try:
        partes = linea.strip().split()
        fecha = partes[0]
        monto = float(partes[-1].replace(",", ""))
        descripcion = " ".join(partes[1:-1])
        return {"Fecha": fecha, "Descripción": descripcion, "Monto": monto}
    except (ValueError, IndexError):
        return None


def extraer_transaccion(linea: str,
                        processor: TransactionProcessor,
                        config: dict) -> dict | None:
    """Extrae los datos de una transacción de una línea de texto."""
    try:
        partes = linea.strip().split()
        fecha = partes[0]
        monto = float(partes[-1].replace(",", ""))
        nombre_sucio = " ".join(partes[1:-1])

        nombre_limpio = processor.extract_company_name(nombre_sucio)
        categoria = determinar_categoria(nombre_limpio, config["categorias"])

        return {
            "Fecha": fecha,
            "Descripción": nombre_limpio,
            "Categoría": categoria,
            "Monto": monto,
            "Tipo": "Ingreso" if monto > 0 else "Gasto",
        }
    except (ValueError, IndexError):
        return None


def determinar_categoria(nombre: str, categorias: dict) -> str:
    """Determina la categoría basándose en el nombre de la transacción."""
    nombre = nombre.lower()
    for categoria, keywords in categorias.items():
        if any(keyword in nombre for keyword in keywords):
            return categoria
    return "Otros"


def guardar_transacciones(transacciones: list, outputs: dict):
    """Guarda las transacciones en archivos CSV separados por tipo."""
    df = pd.DataFrame(transacciones)
    df_gastos = df[df["Tipo"] == "Gasto"]
    df_ingresos = df[df["Tipo"] == "Ingreso"]

    df_gastos.to_csv(outputs.get("gastos", "gastos.csv"), index=False)
    df_ingresos.to_csv(outputs.get("ingresos", "ingresos.csv"), index=False)
    df.to_csv(outputs.get("todas", "todas_transacciones.csv"), index=False)

    print("✅ Archivos CSV creados con éxito:")


if __name__ == "__main__":
    config = load_config()
    procesar_pdf_a_csv(config["pdf_path"], config)
