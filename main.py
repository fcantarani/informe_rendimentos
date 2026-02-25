"""
main.py
-------
Ponto de entrada da aplicação.

Uso:
  python main.py --split               # dividir PDFs na pasta input/
  python main.py --send                # enviar e-mails dos PDFs em output/
  python main.py --split --send        # executar ambas etapas
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
        logger.warning("Nenhum PDF encontrado em: %s", INPUT_DIR.resolve())
        logger.info("Coloque o arquivo na pasta 'input/' e execute novamente.")
        sys.exit(0)

    processor = PDFProcessor(output_dir=OUTPUT_DIR)
    arquivos_gerados: list[Path] = []

    for pdf in pdfs:
        logging.info("\n%s", '─' * 60)
        resultado = processor.process(pdf)
        arquivos_gerados.extend(resultado.arquivos_gerados)
        logging.info("  Resumo: %d páginas → %d arquivos", resultado.total_pages, resultado.total_files)

    logging.info("\n%s", '═' * 60)
    logging.info("  Total  : %d arquivo(s) em %s", len(arquivos_gerados), OUTPUT_DIR.resolve())
    return arquivos_gerados


# ── Module 2: Send Emails ───────────────────────────────────────────────────

def enviar_emails(files: list[Path] | None = None) -> None:
    """Sends an email for each PDF in the output/ folder using Oracle data."""
    if files is None:
        files = sorted(OUTPUT_DIR.glob("*.pdf"))

    if not files:
        logging.warning("Nenhum PDF encontrado em: %s", OUTPUT_DIR.resolve())
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
    logger.info("  Enviando e-mails para %d arquivo(s)...", len(files))
    logger.info("%s", "═" * 60)

    for pdf in files:
        id_number = re.sub(r"\D", "", pdf.stem)  # strip non-digits
        account = db.get_account(id_number)

        if not account:
            logging.warning("[N/F] %s — não encontrado no Oracle", id_number)
            not_found += 1
            continue

        name  = account.get("nome", "Client")
        email = account.get("email", "")

        if not email:
            logging.warning("[S/E] %s — nenhum e-mail cadastrado", id_number)
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
            logging.error("[ERRO] %s: %s", pdf.name, e)
            pdf.rename(SENT_FAILURE / pdf.name)
            errors += 1

    logger.info("\n%s", "═" * 60)
    logger.info("  Enviados     : %d", sent_count)
    logger.info("  Não encontrados / sem e-mail : %d", not_found)
    logger.info("  Erros        : %d", errors)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    # configure root logger: console + file
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("informe.log", encoding="utf-8"),
        ],
    )
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Processador de PDF e envio de e-mails para informes de rendimento",
    )
    parser.add_argument(
        "--split", "--processar",
        dest="split",
        action="store_true",
        help="[split|processar] Divide PDFs na pasta input/ por CPF/CNPJ",
    )
    parser.add_argument(
        "--send", "--enviar",
        dest="send",
        action="store_true",
        help="[send|enviar] Envia e-mails para documentos na pasta output/",
    )

    args = parser.parse_args()

    if not args.split and not args.send:
        parser.print_help()
        sys.exit(0)

    files: list[Path] | None = None

    if args.split:
        files = split_pdfs()

    if args.send:
        enviar_emails(files)


if __name__ == "__main__":
    main()
