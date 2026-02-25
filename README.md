# Processador de Informe de Rendimentos

Utilitário Python simples que divide relatórios em lote (PDF) por CPF/CNPJ
e envia documentos individualizados por e-mail (AWS SES ou SMTP).

## Funcionalidades

* Análise de PDF com `PyMuPDF` e `pypdf`.
* Extração de identificadores conforme regras de negócio (CPF/CNPJ).
* Consulta a banco Oracle para obter nome e e-mail do cliente.
* Envio de e-mails via AWS SES (com modo de teste).
* Estrutura de pastas em português e configurável via `.env`.

## Começando

1. **Clone o repositório** e ative o ambiente virtual Python:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Configuração**
   * Copie `.env.example` para `.env` e preencha os valores necessários.
   * O projeto usa [`pydantic.BaseSettings`](config/settings.py); as
     variáveis de ambiente são carregadas automaticamente.
   * Campos obrigatórios incluem credenciais do Oracle e chaves AWS SES.
   * Configurações SMTP opcionais são ignoradas por padrão, mas ficam
     disponíveis para uso futuro.

3. **Preparar diretórios**
   * Coloque os PDFs fonte em `input/`.
   * Os arquivos de saída serão gerados em `output/` e movidos para as
     subpastas de `sent/` após as tentativas de envio.

4. **Executar a ferramenta**
   ```powershell
   python main.py --split   # dividir PDFs
   python main.py --send    # enviar e-mails
   python main.py --split --send
   ```

5. **Logs**
   * A aplicação usa o módulo padrão `logging`; mensagens aparecem no
     console e também são registradas em `informe.log` na raiz do
     projeto. Você pode monitorar ou rotacionar esse arquivo conforme
     necessário.

## Estrutura do código

```
config/        # gerenciamento de configurações
src/
  database.py         # acesso ao Oracle
  email_sender.py     # helper de e-mail via SES
  identifier.py       # extrator CPF/CNPJ
  pdf_processor.py    # lógica de divisão de PDF
main.py               # ponto de entrada CLI
templates/            # modelo de e-mail HTML
input/ output/ sent/  # diretórios de trabalho
```

## Sugestões para melhoria

* Testes automatizados (não incluídos por solicitação atual).
* Substituir OracleDB por uma interface para facilitar mocking.
* Adicionar argumento CLI para caminho personalizado de template.
* Tratar PDFs muito grandes de forma streaming.

## Licença

Modelo MIT (ou outra apropriada). Certifique-se de não commitar
informações sensíveis no repositório.
