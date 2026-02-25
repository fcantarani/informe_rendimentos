"""
src/database.py
---------------
Oracle database access layer.
Dependency: oracledb (pip install oracledb)
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
                self.__log.info("Oracle connection established.")
            else:
                logging.info("Oracle connection established.")
        except Exception as e:
            if self.__log:
                self.__log.error(f"Connection error: {e}")
            else:
                logging.error(f"Connection error: {e}")
            raise

    def ensure_connection(self):
        """Check that connection is alive; reconnect if needed."""        try:
            self.__connection.ping()
        except Exception:
            logging.info("Reconnecting...")
            self.__connect()

    def fechar(self):
        """Encerra cursor e conexão."""
        try:
            if self.__cursor:
                self.__cursor.close()
            if self.__connection:
                self.__connection.close()
            logging.info("Oracle connection closed.")
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
                self.__log.error(f"Query execution error: {e}")
            else:
                logging.error(f"Query execution error: {e}")
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
                self.__log.error(f"Query execution error: {e}")
            else:
                logging.error(f"Query execution error: {e}")
            return []

    def testar_conexao(self) -> bool:
        """Run SELECT 1 FROM DUAL to verify the connection."""        resultado = self.execute_query("SELECT 1 FROM DUAL")
        if resultado is not None:
            logging.info("[DB] connection OK. DUAL → %s", resultado)
            return True
        logging.warning("[DB] connection failure.")
        return False

    def buscar_correntista(self, inscricao: str) -> dict | None:
        """
        Retrieve NAME and EMAIL of an account holder by normalized CPF/CNPJ.
        `inscricao` must contain digits only (no '.', '/', '-').
        Returns first matching record or None.
        """        sql = "SELECT NOME, EMAIL FROM MATERA_CORRENTISTAS WHERE INSCRICAO = :1"
        rows = self.executar(sql, [inscricao])
        return rows[0] if rows else None
