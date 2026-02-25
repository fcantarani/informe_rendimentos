"""
src/email_sender.py
-------------------
Envia e-mails via AWS SES usando um modelo HTML e anexo PDF opcional.
A configuração é obtida do objeto `settings` compartilhado.
"""

from __future__ import annotations

import logging
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from string import Template

import boto3
from botocore.exceptions import ClientError

from config.settings import settings

class EmailSender:
    """
    Envia e-mails HTML (modelo) com anexo PDF opcional usando AWS SES.
    Configuração carregada de settings:
        AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, EMAIL_FROM

    Variáveis de modelo disponíveis:
        $customer_name, $company_name, $ano_atual
    """

    def __init__(self, template_path: Path) -> None:
        cfg = settings
        self._access_key  = cfg.AWS_ACCESS_KEY_ID or ""
        self._secret_key  = cfg.AWS_SECRET_ACCESS_KEY or ""
        self._region      = cfg.AWS_REGION
        self._from        = cfg.EMAIL_FROM or "auto_bko@claropay.com.br"
        self._modo_teste  = cfg.MODO_TESTE
        self._email_teste = cfg.EMAIL_TESTE or ""
        self._template    = self._load_template(template_path)

    # ── template ──────────────────────────────────────────────────────────────

    @staticmethod
    def _load_template(path: Path) -> Template:
        if not path.exists():
            raise FileNotFoundError(f"Modelo não encontrado: {path}")
        return Template(path.read_text(encoding="utf-8"))

    def _render(self, **variables: str) -> str:
        return self._template.safe_substitute(**variables)

    # ── cliente SES ───────────────────────────────────────────────────────────

    def _ses_client(self):
        return boto3.client(
            "ses",
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
        )

    # ── montagem da mensagem ──────────────────────────────────────────────────

    def _build_message(
        self,
        recipient: str,
        subject: str,
        body_html: str,
        attachment: Path | None,
    ) -> MIMEMultipart:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"]    = self._from
        msg["To"]      = recipient

        msg_body = MIMEMultipart("alternative")
        msg_body.attach(MIMEText(body_html.encode("utf-8"), "html", "utf-8"))
        msg.attach(msg_body)

        if attachment and attachment.exists():
            with open(attachment, "rb") as f:
                parte = MIMEApplication(f.read())
            parte.add_header("Content-Disposition", "attachment", filename=attachment.name)
            msg.attach(parte)

        return msg

    # ── sending helpers ───────────────────────────────────────────────────────

    def send(
        self,
        recipient: str,
        subject: str = "Informe de Rendimentos",
        attachment: Path | None = None,
        **template_vars: str,
    ) -> None:
        """
        Envia um e-mail ao destinatário com o modelo renderizado.

        Args:
            recipient:            endereço de e-mail do destinatário
            subject:              assunto do e-mail
            attachment:           caminho do anexo PDF (opcional)
            **template_vars:      variáveis substituídas no modelo HTML
                                  ex. customer_name="Joao", company_name="XYZ"
        """
        # test mode redirect
        real_recipient = recipient
        if self._modo_teste:
            recipient = self._email_teste
            logging.info("[MODO TESTE] redirecionando %s → %s", real_recipient, recipient)

        body_html = self._render(**template_vars)
        msg = self._build_message(recipient, subject, body_html, attachment)
        client = self._ses_client()

        try:
            response = client.send_raw_email(
                Source=self._from,
                Destinations=[recipient],
                RawMessage={"Data": msg.as_string()},
            )
            logging.info(
                "[EMAIL] enviado → %s%s | MessageId: %s",
                recipient,
                (f" (anexo: {attachment.name})" if attachment else ""),
                response["MessageId"],
            )
        except ClientError as e:
            logging.error(
                "[ERRO] falha ao enviar para %s: %s",
                recipient,
                e.response["Error"]["Message"],
            )
            raise

