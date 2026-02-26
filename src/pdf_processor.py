"""
src/pdf_processor.py
--------------------
Divide um PDF em arquivos individuais, agrupando páginas por CPF/CNPJ
encontrado no conteúdo. Páginas sem identificador herdam o anterior.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from time import perf_counter

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
    started_at: datetime | None = None
    finished_at: datetime | None = None
    elapsed_seconds: float = 0.0

    @property
    def total_files(self) -> int:
        return len(self.generated_files)


class PDFProcessor:
    """
    Processa um arquivo PDF, agrupando páginas por CPF/CNPJ e gravando
    um PDF de saída por destinatário na pasta de destino.
    """
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self._extractor = ExtractorIdentifier()

    # ── API pública ────────────────────────────────────────────────────────────

    def process(self, caminho_pdf: Path) -> ProcessingResult:
        """Processa o PDF e retorna um resumo dos resultados."""
        if not caminho_pdf.exists():
            logging.error("Arquivo não encontrado: %s", caminho_pdf)
            raise FileNotFoundError(f"{caminho_pdf} não encontrado")

        started_at = datetime.now()
        started_perf = perf_counter()

        self.output_dir.mkdir(parents=True, exist_ok=True)

        doc_fitz = fitz.open(str(caminho_pdf))
        leitor   = pypdf.PdfReader(str(caminho_pdf))
        total    = len(leitor.pages)

        logging.info("  Arquivo   : %s", caminho_pdf.name)
        logging.info("  Páginas  : %d", total)

        groups_map  = self._group_pages(doc_fitz, total)
        doc_fitz.close()

        files = self._write_groups(groups_map, leitor)
        finished_at = datetime.now()
        elapsed_seconds = perf_counter() - started_perf

        return ProcessingResult(
            total_pages=total,
            groups=list(groups_map.values()),
            generated_files=files,
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=elapsed_seconds,
        )

    # ── passos internos ────────────────────────────────────────────────────────

    def _group_pages(
        self, doc_fitz: fitz.Document, total: int
    ) -> dict[str, PageGroup]:
        """
        Primeira passagem: lê cada página, extrai o identificador e agrupa.
        Páginas sem CPF/CNPJ herdam o identificador anterior.
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
                logging.info("    [info] página %d: sem id — agrupada com '%s'", i + 1, last_name)
            else:
                # first page had no identifier
                isolated_name = f"pagina_{i + 1}_sem_identificador"
                ident = Identifier(valor=isolated_name, tipo="---")
                logging.warning(
                    "    [AVISO] Página %d: sem identificador e sem página anterior → '%s.pdf'",
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
        Segunda passagem: grava um PDF por grupo contendo todas as páginas agrupadas.
        """
        arquivos: list[Path] = []

        for chave, grupo in groups.items():
            destino = self.output_dir / f"{chave}.pdf"
            escritor = pypdf.PdfWriter()
            for idx in grupo.indices:
                escritor.add_page(leitor.pages[idx])
            with open(destino, "wb") as f:
                escritor.write(f)

            paginas_str = ", ".join(str(p + 1) for p in grupo.indices)
            logging.info(
                "    [%s] %s  (%d páginas: %s)",
                grupo.identifier.tipo,
                destino.name,
                grupo.count,
                paginas_str,
            )
            arquivos.append(destino)

        return arquivos
