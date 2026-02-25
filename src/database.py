"""
src/database.py
---------------
Camada de acesso ao banco Oracle.
Dependência: oracledb (pip install oracledb)
"""
import logging

import oracledb

from config.settings import settings


class OracleDB:
    def __init__(self, log=None):
        cfg = settings
        self.__dsn      = cfg.ORACLE_DSN
        self.__username = cfg.ORACLE_USER
        self.__password = cfg.ORACLE_PWD
        self.__log      = log
        self.__connection = None
        self.__cursor     = None
        self.__connect()

    # ── conexão ────────────────────────────────────────────────────────────────

    def __connect(self):
        try:
            self.__connection = oracledb.connect(
                user=self.__username,
                password=self.__password,
                dsn=self.__dsn,
            )
            self.__cursor = self.__connection.cursor()
            if self.__log:
                self.__log.info("Conexão com Oracle estabelecida.")
            else:
                logging.info("Conexão com Oracle estabelecida.")
        except Exception as e:
            if self.__log:
                self.__log.error(f"Erro de conexão: {e}")
            else:
                logging.error(f"Erro de conexão: {e}")
            raise

    def ensure_connection(self):
        """Check that connection is alive; reconnect if needed."""
        try:
            self.__connection.ping()
        except Exception:
            logging.info("Reconectando...")
            self.__connect()

    def fechar(self):
        """Encerra cursor e conexão."""
        try:
            if self.__cursor:
                self.__cursor.close()
            if self.__connection:
                self.__connection.close()
            logging.info("Conexão com Oracle encerrada.")
        except Exception:
            pass
        finally:
            self.__cursor     = None
            self.__connection = None

    # ── context manager ────────────────────────────────────────────────────────

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.fechar()

    # ── queries ────────────────────────────────────────────────────────────────

    def execute_query(self, query: str, params=None):
        """
        Executa uma query e retorna lista de tuplas (raw).
        Retorna None em caso de erro.
        """
        try:
            self.__cursor.execute(query, params or [])
            return self.__cursor.fetchall()
        except Exception as e:
            if self.__log:
                self.__log.error(f"Erro ao executar consulta: {e}")
            else:
                logging.error(f"Erro ao executar consulta: {e}")
            return None

    def executar(self, query: str, params=None) -> list[dict]:
        """
        Executa uma query e retorna lista de dicts {coluna: valor}.
        Facilita o acesso por nome de coluna.
        """
        try:
            self.__cursor.execute(query, params or [])
            colunas = [col[0].lower() for col in self.__cursor.description]
            return [dict(zip(colunas, row)) for row in self.__cursor.fetchall()]
        except Exception as e:
            if self.__log:
                self.__log.error(f"Erro ao executar consulta: {e}")
            else:
                logging.error(f"Erro ao executar consulta: {e}")
            return []

    def testar_conexao(self) -> bool:
        """Executa SELECT 1 FROM DUAL para verificar a conexão."""
        resultado = self.execute_query("SELECT 1 FROM DUAL")
        if resultado is not None:
            logging.info("[DB] conexão OK. DUAL → %s", resultado)
            return True
        logging.warning("[DB] falha na conexão.")
        return False

    def get_account(self, registration: str) -> dict | None:
        """
        Recupera NOME e EMAIL de um correntista por CPF/CNPJ normalizado.
        `registration` deve conter apenas dígitos (sem '.', '/', '-').
        Retorna o primeiro registro correspondente ou None.
        """
        sql = "SELECT NOME, EMAIL FROM MATERA_CORRENTISTAS WHERE INSCRICAO = :1"
        rows = self.executar(sql, [registration])
        return rows[0] if rows else None
