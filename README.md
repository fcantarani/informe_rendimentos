# Informe de Rendimentos Processor

Small Python utility that splits bulk PDF reports by CPF/CNPJ and sends
individualized documents via email (AWS SES or SMTP).

## Features

* PDF parsing with `PyMuPDF` and `pypdf`.
* Identifier extraction according to business rules (CPF/CNPJ).
* Oracle database lookup for client name/email.
* Email delivery through AWS SES (with test mode).
* English-only directory structure and configurable via `.env`.

## Getting started

1. **Clone repository** and activate Python virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Configuration**
   * Copy `.env.example` to `.env` and fill in required values.
   * The project uses [`pydantic.BaseSettings`](config/settings.py); the
     environment variables are loaded automatically.
   * Required entries include Oracle credentials and AWS SES keys.
   * Optional SMTP settings are ignored by default but available for
     future use.

3. **Prepare directories**
   * Place the source PDF(s) into `input/`.
   * Output files will be generated in `output/` and moved to `sent/`
     subfolders after email attempts.

4. **Run the tool**
   ```powershell
   python main.py --split   # split PDFs
   python main.py --send    # send emails
   python main.py --split --send
   ```

5. **Logs**
   * The application uses the standard `logging` module; messages appear
     on the console with timestamps and log levels.

## Code structure

```
config/        # settings management
src/
  database.py  # Oracle access
  email_sender.py # SES-based email helper
  identifier.py   # CPF/CNPJ extractor
  pdf_processor.py# PDF splitting logic
main.py        # CLI entry point
templates/     # HTML email template
input/ output/ sent/  # working directories
```

## Suggestions for further improvement

* Automated tests (not included per current request).
* Replace OracleDB with an interface for easier mocking.
* Add a CLI argument for custom template paths.
* Handle very large PDFs in streaming fashion.

## License

MIT-style (or whatever is appropriate). Ensure you do not commit
sensitive information to the repository.
