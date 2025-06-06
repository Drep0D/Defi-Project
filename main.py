import pdfplumber
import pandas as pd
from model.processor import TransactionProcessor
# Actualizacion para ver si se sube a git

def procesar_pdf_a_csv(pdf_path: str):
    """
    Procesa un extracto bancario PDF y genera archivos CSV con las transacciones.
    
    Args:
        pdf_path (str): Ruta al archivo PDF a procesar
    """
    # Inicializar el procesador de transacciones
    processor = TransactionProcessor()
    
    transacciones = []

    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                lineas = texto.split('\n')
                for linea in lineas:
                    if es_linea_transaccion(linea):
                        transaccion = extraer_transaccion(linea, processor)
                        if transaccion:
                            transacciones.append(transaccion)

    # Convertir a DataFrame y guardar archivos
    guardar_transacciones(transacciones)

def es_linea_transaccion(linea: str) -> bool:
    """Determina si una línea contiene una transacción bancaria"""
    return ('/' in linea and 
            any(char.isdigit() for char in linea) and
            len(linea.split()) >= 3)

def extraer_transaccion(linea: str, processor: TransactionProcessor) -> dict:
    """
    Extrae los datos de una transacción de una línea de texto.
    
    Args:
        linea (str): Línea de texto del PDF
        processor (TransactionProcessor): Instancia del procesador de nombres
    
    Returns:
        dict: Diccionario con los datos de la transacción o None si hay error
    """
    try:
        partes = linea.strip().split()
        fecha = partes[0]
        monto = float(partes[-1].replace(",", ""))
        nombre_sucio = ' '.join(partes[1:-1])
        
        # Usar el procesador para limpiar el nombre
        nombre_limpio = processor.extract_company_name(nombre_sucio)
        
        # Determinar categoría automáticamente
        categoria = determinar_categoria(nombre_limpio)
        
        return {
            'Fecha': fecha,
            'Descripción': nombre_limpio,
            'Categoría': categoria,
            'Monto': monto,
            'Tipo': 'Ingreso' if monto > 0 else 'Gasto'
        }
    except (ValueError, IndexError) as e:
        print(f"⚠️ Error procesando línea: {linea} - {e}")
        return None

def determinar_categoria(nombre: str) -> str:
    """Determina la categoría basándose en el nombre de la transacción"""
    nombre = nombre.lower()
    categorias = {
        'Comida': ['mcdonald', 'starbucks', 'don julios', 'wawa', 'panera', 'hibachi'],
        'Compras': ['walmart', 'ross', 'aldi', 'home depot', 'sams club'],
        'Transporte': ['lyft', 'uber', 'sunpass', 'racetrac'],
        'Entretenimiento': ['netflix', 'spotify', 'youtube', 'steam'],
        'Servicios': ['spectrum', 'paypal', 'zelle'],
        'Salud': ['gym', 'vitamin', 'farmacia'],
        'Transferencia': ['zelle', 'transfer'],
        'Nómina': ['square', 'payroll'],
        'Otros': []
    }
    
    for categoria, keywords in categorias.items():
        if any(keyword in nombre for keyword in keywords):
            return categoria
    return 'Otros'

def guardar_transacciones(transacciones: list):
    """
    Guarda las transacciones en archivos CSV separados por tipo
    
    Args:
        transacciones (list): Lista de diccionarios con transacciones
    """
    df = pd.DataFrame(transacciones)
    
    # Filtrar y guardar gastos
    df_gastos = df[df['Tipo'] == 'Gasto'].copy()
    df_gastos.to_csv("gastos.csv", index=False)
    
    # Filtrar y guardar ingresos
    df_ingresos = df[df['Tipo'] == 'Ingreso'].copy()
    df_ingresos.to_csv("ingresos.csv", index=False)
    
    # Opcional: guardar todas las transacciones
    df.to_csv("todas_transacciones.csv", index=False)
    
    print("✅ Archivos CSV creados con éxito:")
    print(f"- gastos.csv ({len(df_gastos)} transacciones)")
    print(f"- ingresos.csv ({len(df_ingresos)} transacciones)")

if __name__ == "__main__":
    # Configuración
    pdf_path = "Est_cuenta.pdf"  # Cambia esto por tu ruta real
    
    # Procesar el PDF
    procesar_pdf_a_csv(pdf_path)