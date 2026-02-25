"""
src/identifier.py
-----------------
Responsável por extrair números de CPF e CNPJ do texto de páginas de PDF.

Regras de negócio para informes de rendimento:
  * ≥2 CNPJs → 2.º CNPJ é o destinatário (empresa)
  * 1 CNPJ   → ignorar; usar CPF em vez (destinatário pessoa física)
  * 0 CNPJ   → usar o primeiro CPF encontrado
"""
import re
from dataclasses import dataclass


# ── Padrões ────────────────────────────────────────────────────────────────────
_CNPJ_RE = re.compile(r"\b(\d{2}[.\s]?\d{3}[.\s]?\d{3}[/\s]?\d{4}[-\s]?\d{2})\b")
_CPF_RE  = re.compile(r"\b(\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2})\b")


@dataclass
class Identifier:
    valor: str
    tipo: str          # "CPF" | "CNPJ" | ""

    def __bool__(self) -> bool:
        return bool(self.valor)

    def __str__(self) -> str:
        return self.valor

    @property
    def nome_arquivo(self) -> str:
        """Return value with invalid Windows characters replaced."""
        return re.sub(r'[\\/*?:"<>|]', "_", self.valor)


class ExtractorIdentifier:
    """Extract CPF/CNPJ values from a text block according to business rules."""
    # ── helpers de formatação ──────────────────────────────────────────────────
    @staticmethod
    def _fmt_cnpj(raw: str) -> str:
        return f"{raw[:2]}.{raw[2:5]}.{raw[5:8]}/{raw[8:12]}-{raw[12:]}"

    @staticmethod
    def _fmt_cpf(raw: str) -> str:
        return f"{raw[:3]}.{raw[3:6]}.{raw[6:9]}-{raw[9:]}"

    # ── extratores brutos ──────────────────────────────────────────────────────
    def _cnpjs(self, text: str) -> list[str]:
        result = []
        for m in _CNPJ_RE.finditer(text):
            raw = re.sub(r"[^\d]", "", m.group(1))
            if len(raw) == 14:
                result.append(self._fmt_cnpj(raw))
        return result

    def _cpf(self, text: str) -> str | None:
        m = _CPF_RE.search(text)
        if m:
            raw = re.sub(r"[^\d]", "", m.group(1))
            if len(raw) == 11:
                return self._fmt_cpf(raw)
        return None

    # ── public interface ─────────────────────────────────────────────────────
    def extract(self, text: str) -> Identifier:
        """
        Apply business rules and return an Identifier.

        Rules:
          1. ≥2 CNPJs → use 2nd CNPJ (company recipient)
          2. 1 CNPJ   → try CPF first, otherwise fallback to CNPJ
          3. 0 CNPJ   → use first CPF found
        """
        cnpjs = self._cnpjs(text)

        if len(cnpjs) >= 2:
            return Identifier(valor=cnpjs[1], tipo="CNPJ")

        cpf = self._cpf(text)
        if cpf:
            return Identifier(valor=cpf, tipo="CPF")

        if len(cnpjs) == 1:
            return Identifier(valor=cnpjs[0], tipo="CNPJ")   # fallback

        return Identifier(valor="", tipo="")
