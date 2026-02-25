"""
main.py
-------
Entry point for the application.

Usage:
  python main.py --split               # split PDFs in input/ folder
  python main.py --send                # send emails for PDFs in output/
  python main.py --split --send        # perform both steps
"""

import argparse
import logging
import re
import sys
from pathlib import Path

from config import settings
from config.settings import (
    INPUT_DIR,
    OUTPUT_DIR,
    SENT_DIR,
    SENT_SUCCESS,
    SENT_FAILURE,
    TEMPLATE_DIR,
    NOME_EMPRESA,
    ANO_CALENDARIO,
)
from src.pdf_processor import PDFProcessor
from src.database import OracleDB
from src.email_sender import EmailSender


# ── Module 1: Split PDFs ─────────────────────────────────────────────────────

def split_pdfs() -> list[Path]:
    """Split all PDFs from input/ by CPF/CNPJ into output/."""
    logger = logging.getLogger("main.split")
    pdfs = sorted(INPUT_DIR.glob("*.pdf"))

    if not pdfs:
        logger.warning("No PDFs found in: %s", INPUT_DIR.resolve())
        logger.info("Place the file in the 'input/' folder and run again.")
        sys.exit(0)

    processor = PDFProcessor(output_dir=OUTPUT_DIR)
    arquivos_gerados: list[Path] = []

    for pdf in pdfs:
        logging.info("\n%s", '─' * 60)
        resultado = processor.process(pdf)
        arquivos_gerados.extend(resultado.arquivos_gerados)
        logging.info("  Summary: %d pages → %d files", resultado.total_pages, resultado.total_files)

    logging.info("\n%s", '═' * 60)
    logging.info("  Total  : %d file(s) in %s", len(arquivos_gerados), OUTPUT_DIR.resolve())
    return arquivos_gerados


# ── Module 2: Send Emails ───────────────────────────────────────────────────

def enviar_emails(files: list[Path] | None = None) -> None:
    """Sends an email for each PDF in the output/ folder using Oracle data."""
    if files is None:
        files = sorted(OUTPUT_DIR.glob("*.pdf"))

    if not files:
        logging.warning("No PDFs found in: %s", OUTPUT_DIR.resolve())
        return

    SENT_DIR.mkdir(exist_ok=True)
    SENT_SUCCESS.mkdir(exist_ok=True)
    SENT_FAILURE.mkdir(exist_ok=True)

    logger = logging.getLogger("main.enviar")
    db     = OracleDB(log=logger)
    sender = EmailSender(template_path=TEMPLATE_DIR / "informe.html")
    ano    = ANO_CALENDARIO or "2025"
    company = NOME_EMPRESA or "ClaroPay"

    sent_count = errors = not_found = 0  # renamed for clarity

    logger.info("\n%s", "═" * 60)
    logger.info("  Sending emails for %d file(s)...", len(arquivos))
    logger.info("%s", "═" * 60)

    for pdf in files:
        id_number = re.sub(r"\D", "", pdf.stem)  # strip non-digits
        account = db.get_account(id_number)

        if not account:
            logging.warning("[N/F] %s — not found in Oracle", id_number)
            not_found += 1
            continue

        name  = account.get("nome", "Client")
        email = account.get("email", "")

        if not email:
            logging.warning("[S/E] %s — no email registered", id_number)
            not_found += 1
            continue

        try:
            sender.send(
                recipient=email,
                subject=f"Income Report {ano} — {company}",
                attachment=pdf,
                customer_name=name,
                company_name=company,
                ano_atual=str(__import__("datetime").date.today().year),
            )
            pdf.rename(SENT_SUCCESS / pdf.name)
            sent_count += 1
        except Exception as e:
            logging.error("[ERROR] %s: %s", pdf.name, e)
            pdf.rename(SENT_FAILURE / pdf.name)
            errors += 1

    logger.info("\n%s", "═" * 60)
    logger.info("  Sent         : %d", sent_count)
    logger.info("  Not found / no email: %d", not_found)
    logger.info("  Errors       : %d", errors)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="PDF processor and email sender for income reports",
    )
    parser.add_argument(
        "--split", "--processar",
        dest="split",
        action="store_true",
        help="[split|processar] Split PDFs in the input/ folder by CPF/CNPJ",
    )
    parser.add_argument(
        "--send", "--enviar",
        dest="send",
        action="store_true",
        help="[send|enviar] Send emails for documents in the output/ folder",

    args = parser.parse_args()

    if not args.split and not args.send:
        parser.print_help()
        sys.exit(0)

    arquivos: list[Path] | None = None

    if args.split:
        arquivos = split_pdfs()

    if args.send:
        enviar_emails(arquivos)


if __name__ == "__main__":
    main()
