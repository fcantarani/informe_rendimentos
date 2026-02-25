"""
src/pdf_processor.py
--------------------
Splits a PDF into individual files, grouping pages by CPF/CNPJ
found in the content. Pages without an identifier inherit the previous one.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import fitz      # PyMuPDF — text extraction
import pypdf     # pypdf   — PDF read/write

from src.identifier import ExtractorIdentifier, Identifier


@dataclass
class PageGroup:
    identifier: Identifier
    indices: list[int] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.indices)


@dataclass
class ProcessingResult:
    total_pages: int
    groups: list[PageGroup]
    generated_files: list[Path] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.generated_files)


class PDFProcessor:
    """
    Process a PDF file, grouping pages by CPF/CNPJ and writing
    one output PDF per recipient in the target folder.
    """
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self._extractor = ExtractorIdentifier()

    # ── API pública ────────────────────────────────────────────────────────────

    def process(self, caminho_pdf: Path) -> ProcessingResult:
        """Process the PDF and return a result summary."""
        if not caminho_pdf.exists():
            logging.error("File not found: %s", caminho_pdf)
            raise FileNotFoundError(f"{caminho_pdf} not found")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        doc_fitz = fitz.open(str(caminho_pdf))
        leitor   = pypdf.PdfReader(str(caminho_pdf))
        total    = len(leitor.pages)

        logging.info("  File   : %s", caminho_pdf.name)
        logging.info("  Pages  : %d", total)

        groups_map  = self._group_pages(doc_fitz, total)
        doc_fitz.close()

        files = self._write_groups(groups_map, leitor)
        return ProcessingResult(
            total_pages=total,
            groups=list(groups_map.values()),
            generated_files=files,
        )

    # ── passos internos ────────────────────────────────────────────────────────

    def _group_pages(
        self, doc_fitz: fitz.Document, total: int
    ) -> dict[str, PageGroup]:
        """
        First pass: read each page, extract identifier and group.
        Pages without CPF/CNPJ inherit the previous identifier.
        """
        groups: dict[str, PageGroup] = {}
        last_name: str | None = None
        last_id:   Identifier | None = None

        for i in range(total):
            text = doc_fitz[i].get_text()
            ident = self._extractor.extract(text)

            if ident:
                last_id   = ident
                last_name = ident.nome_arquivo
            elif last_name and last_id:
                # inherits previous identifier
                ident = last_id
                logging.info("    [info] page %d: no id — grouped with '%s'", i + 1, last_name)
            else:
                # first page had no identifier
                isolated_name = f"page_{i + 1}_no_identifier"
                ident = Identifier(valor=isolated_name, tipo="---")
                logging.warning(
                    "    [WARNING] Page %d: no identifier and no previous page → '%s.pdf'",
                    i + 1,
                    isolated_name,
                )

            key = ident.nome_arquivo
            if key not in groups:
                groups[key] = PageGroup(identifier=ident)
            groups[key].indices.append(i)

        return groups

    def _write_groups(
        self,
        groups: dict[str, PageGroup],
        leitor: pypdf.PdfReader,
    ) -> list[Path]:
        """
        Second pass: write a PDF per group containing all grouped pages.
        """        arquivos: list[Path] = []

        for chave, grupo in groups.items():
            destino = self.output_dir / f"{chave}.pdf"
            escritor = pypdf.PdfWriter()
            for idx in grupo.indices:
                escritor.add_page(leitor.pages[idx])
            with open(destino, "wb") as f:
                escritor.write(f)

            paginas_str = ", ".join(str(p + 1) for p in grupo.indices)
            logging.info(
                "    [%s] %s  (%d pages: %s)",
                grupo.identifier.tipo,
                destino.name,
                grupo.count,
                paginas_str,
            )
            arquivos.append(destino)

        return arquivos
