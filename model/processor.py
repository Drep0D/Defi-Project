from transformers import pipeline
import re
from typing import Optional, List, Dict

ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)


class TransactionProcessor:
    def __init__(self, common_companies: Optional[Dict[str, List[str]]] = None):
        self.common_companies = common_companies or self._load_common_companies()

    @staticmethod
    def _load_common_companies() -> Dict[str, List[str]]:
        """Diccionario de compañías comunes y sus variantes."""
        return {
            "mcdonalds": ["mcdonald's", "mcdonalds"],
            "starbucks": ["starbucks"],
            "walmart": ["walmart", "wal-mart"],
            "netflix": ["netflix"],
            "amazon": ["amazon.com", "amazon"],
            "don julios": ["don julios", "tst*don julios"],
            "square": ["square inc"],
            "zelle": ["zelle payment"],
        }

    PATRONES_DESCARTADOS = [
        r"DES:.*? ",
        r"ID:.*? ",
        r"INDN:.*? ",
        r"CO ID:.*? ",
        r"\d{4,}",
        r"[#*]?[0-9A-Z]{5,}",
        r"PPD|WEB|CCD|POS|RECURRING|PURCHASE|MOBILE|CHECKCARD",
    ]

    def limpiar_texto(self, texto: str) -> str:
        """Limpia el texto quitando patrones no deseados."""
        texto = texto.upper()
        for patron in self.PATRONES_DESCARTADOS:
            texto = re.sub(patron, "", texto)
        return texto.strip()

    def extract_company_name(self, texto_original: str) -> str:
        """Extrae el nombre de la compañía."""
        texto_limpio = self.limpiar_texto(texto_original)

        company = self._extract_with_regex(texto_limpio)
        if company:
            return company

        company = self._match_known_companies(texto_limpio.lower())
        if company:
            return company

        company = self._extract_with_ner(texto_limpio)
        if company:
            return company

        return self._extract_fallback(texto_limpio)

    def _extract_with_regex(self, texto: str) -> Optional[str]:
        """Intenta extraer el nombre con patrones regex específicos."""
        patterns = [
            r'(?:MOBILE\\s*PURCHASE\\s*\\d{4}\\s*)(.*?)(?:\\s*[A-Z0-9]{4,}\\s+[A-Z]+\\s+[A-Z]+|\\s*\\d+|$)',
            r'(?:CHECKCARD\\s*\\d{4}\\s*)(?:[A-Z]+\\*)?(.*?)(?:\\s*-[A-Z]*|\\s+[A-Z]{2}\\s*|\\s*\\d+|$)',
            r'(?:PURCHASE\\s*\\d{4}\\s*)(?:[A-Z]+\\*)?(.*?)(?:\\s*\\d{10,}|$)',
            r'(?:ZELLE\\s*PAYMENT\\s*FROM\\s*)(.*?)(?:\\s*CONF\\#|$)',
            r'(?:[A-Z]+\\s*INC\\s*)(.*?)(?:\\s*DES:|$)',
        ]
            
        for pattern in patterns:
            match = re.search(pattern, texto)
            if match:
                company = match.group(1).strip()
                return self._clean_company_name(company)
        return None

    def _match_known_companies(self, texto: str) -> Optional[str]:
        """Busca coincidencias con compañías conocidas."""
        for company_name, variants in self.common_companies.items():
            for variant in variants:
                if variant in texto:
                    return self._clean_company_name(company_name)
        return None

    def _extract_with_ner(self, texto: str) -> Optional[str]:
        """Usa el modelo NER para extraer nombres de organizaciones."""
        entidades = ner_pipeline(texto)
        for ent in entidades:
            if ent["entity_group"] in ["ORG", "MISC"]:
                return self._clean_company_name(ent["word"])
        return None

    def _extract_fallback(self, texto: str) -> str:
        """Último recurso para extraer el nombre."""
        cleaned = re.sub(r"[0-9#*]+", " ", texto)
        palabras = [w for w in cleaned.split() if len(w) > 2][:4]
        return self._clean_company_name(" ".join(palabras))

    @staticmethod
    def _clean_company_name(name: str) -> str:
        """Normaliza el nombre de la compañía."""
        name = re.sub(r"^[*#\\- ]+|[ -*#]+$", "", name.strip())
        return name.title()
