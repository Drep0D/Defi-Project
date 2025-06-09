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