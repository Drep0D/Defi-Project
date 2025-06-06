from transformers import pipeline
import re
from typing import Optional, List, Dict
# import joblib

# Cargamos el modelo de Hugging Face para detectar nombres de empresas y organizaciones
ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)

class TransactionProcessor:
    def __init__(self):
        self.common_companies = self._load_common_companies()
        
    @staticmethod
    def _load_common_companies() -> Dict[str, List[str]]:
        """Diccionario de compañías comunes y sus variantes"""
        return {
            'mcdonalds': ["mcdonald's", "mcdonalds"],
            'starbucks': ["starbucks"],
            'walmart': ["walmart", "wal-mart"],
            'netflix': ["netflix"],
            'amazon': ["amazon.com", "amazon"],
            'don julios': ["don julios", "tst*don julios"],
            'square': ["square inc"],
            'zelle': ["zelle payment"],
            # Añade más compañías comunes según necesites
        }
    
    # Patrones de texto que queremos eliminar
    PATRONES_DESCARTADOS = [
        r"DES:.*? ", r"ID:.*? ", r"INDN:.*? ", r"CO ID:.*? ",
        r"\d{4,}", r"[#*]?[0-9A-Z]{5,}", r"PPD|WEB|CCD|POS|RECURRING|PURCHASE|MOBILE|CHECKCARD"
    ]
    
    def limpiar_texto(self, texto: str) -> str:
        """Limpia el texto quitando patrones no deseados"""
        texto = texto.upper()
        for patron in self.PATRONES_DESCARTADOS:
            texto = re.sub(patron, '', texto)
        return texto.strip()
    
    def extract_company_name(self, texto_original: str) -> str:
        """
        Extrae el nombre de la compañía combinando regex, compañías conocidas y el modelo NER.
        
        Args:
            texto_original: Descripción de la transacción bancaria
            
        Returns:
            Nombre normalizado de la compañía
        """
        # 1. Limpieza inicial del texto
        texto_limpio = self.limpiar_texto(texto_original)
        
        # 2. Intentar extraer con patrones regex específicos
        company = self._extract_with_regex(texto_limpio)
        if company:
            return company
            
        # 3. Buscar coincidencias con compañías conocidas
        company = self._match_known_companies(texto_limpio.lower())
        if company:
            return company
            
        # 4. Usar el modelo NER de Hugging Face
        company = self._extract_with_ner(texto_limpio)
        if company:
            return company
            
        # 5. Último recurso: extraer las primeras palabras relevantes
        return self._extract_fallback(texto_limpio)
    
    def _extract_with_regex(self, texto: str) -> Optional[str]:
        """Intenta extraer el nombre con patrones regex específicos"""
        patterns = [
            # Compras móviles: "MOBILE PURCHASE 0120 MCDONALD'S F35402"
            r'(?:MOBILE\s*PURCHASE\s*\d{4}\s*)(.*?)(?:\s*[A-Z0-9]{4,}\s+[A-Z]+\s+[A-Z]+|\s*\d+|$)',
            
            # Compras con tarjeta: "CHECKCARD 1224 TST*DON JULIOS- T TAMPA FL"
            r'(?:CHECKCARD\s*\d{4}\s*)(?:[A-Z]+\*)?(.*?)(?:\s*-[A-Z]*|\s+[A-Z]{2}\s*|\s*\d+|$)',
            
            # Compras genéricas: "PURCHASE 0106 PAYPAL *NETFLIX.COM 8882211161"
            r'(?:PURCHASE\s*\d{4}\s*)(?:[A-Z]+\*)?(.*?)(?:\s*\d{10,}|$)',
            
            # Transferencias Zelle: "ZELLE PAYMENT FROM ANGIE MENESES BUSTAMANTE"
            r'(?:ZELLE\s*PAYMENT\s*FROM\s*)(.*?)(?:\s*CONF\#|$)',
            
            # Depósitos: "SQUARE INC DES:PAYROLL ID:T3MA..."
            r'(?:[A-Z]+\s*INC\s*)(.*?)(?:\s*DES:|$)',
            
            # Patrón para códigos al final: "ROSS STORES #1111 WESLEY CHAPEL FL"
            r'(.*?)(?:\s*#[0-9]+\s+|\s+[A-Z]{2}\s*$)',
            
            # Patrón genérico para nombres comerciales
            r'([A-Z][A-Z\'\s&]+)(?=\s+[A-Z0-9]{4,}|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto)
            if match:
                company = match.group(1).strip()
                return self._clean_company_name(company)
        return None
    
    def _match_known_companies(self, texto: str) -> Optional[str]:
        """Busca coincidencias con compañías conocidas"""
        for company_name, variants in self.common_companies.items():
            for variant in variants:
                if variant in texto:
                    return self._clean_company_name(company_name)
        return None
    
    def _extract_with_ner(self, texto: str) -> Optional[str]:
        """Usa el modelo NER para extraer nombres de organizaciones"""
        entidades = ner_pipeline(texto)
        for ent in entidades:
            if ent['entity_group'] in ['ORG', 'MISC']:
                return self._clean_company_name(ent['word'])
        return None
    
    def _extract_fallback(self, texto: str) -> str:
        """Método de último recurso para extraer el nombre"""
        # Eliminar números y códigos residuales
        cleaned = re.sub(r'[0-9#*]+', ' ', texto)
        # Tomar las primeras 3-4 palabras relevantes como nombre
        palabras = [w for w in cleaned.split() if len(w) > 2][:4]
        return self._clean_company_name(' '.join(palabras))
    
    @staticmethod
    def _clean_company_name(name: str) -> str:
        """Normaliza el nombre de la compañía"""
        # Elimina caracteres especiales al inicio/fin
        name = re.sub(r'^[*#\- ]+|[ -*#]+$', '', name.strip())
        # Convierte a formato título (primera letra mayúscula)
        return name.title()

# Función de compatibilidad con el código antiguo
def limpiar_nombre(texto_original):
    processor = TransactionProcessor()
    return processor.extract_company_name(texto_original)