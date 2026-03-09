"""
logger_config.py
Responsável por:
- Configurar o sistema de logging para toda a aplicação
- Escrever logs em ficheiro e no terminal simultaneamente
- Formatar mensagens com timestamp, nível e módulo
"""

import logging
import os
from datetime import datetime

#  Configuração de Paths 
LOGS_DIR  = "logs"
LOG_FILE  = os.path.join(LOGS_DIR, f"crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

#Níveis de Log por Módulo 
# DEBUG    → detalhe máximo (desenvolvimento)
# INFO     → fluxo normal da aplicação
# WARNING  → algo inesperado mas não crítico
# ERROR    → falha numa operação específica
# CRITICAL → falha que impede a aplicação de continuar


def configurar_logger(nivel_consola: str = "INFO", nivel_ficheiro: str = "DEBUG"):
    """
    Configura o logger raiz com dois handlers:
      - StreamHandler → terminal (nível configurável, default INFO)
      - FileHandler   → ficheiro em logs/ (nível configurável, default DEBUG)

    Parâmetros:
        nivel_consola  : nível mínimo a mostrar no terminal
        nivel_ficheiro : nível mínimo a guardar no ficheiro de log
    """

    # Criar diretório de logs se não existir
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    # Formato das mensagens
    formato = "%(asctime)s [%(levelname)-8s] %(module)-22s → %(message)s"
    data_formato = "%Y-%m-%d %H:%M:%S"

    # Handler: Terminal
    handler_consola = logging.StreamHandler()
    handler_consola.setLevel(getattr(logging, nivel_consola.upper(), logging.INFO))
    handler_consola.setFormatter(logging.Formatter(formato, datefmt=data_formato))

    #  Handler: Ficheiro 
    handler_ficheiro = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler_ficheiro.setLevel(getattr(logging, nivel_ficheiro.upper(), logging.DEBUG))
    handler_ficheiro.setFormatter(logging.Formatter(formato, datefmt=data_formato))

    # Logger Raiz 
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # captura tudo, handlers filtram
    logger.handlers.clear()         # evita handlers duplicados
    logger.addHandler(handler_consola)
    logger.addHandler(handler_ficheiro)

    logging.info(f"[Logger] Logging iniciado → ficheiro: {LOG_FILE}")
    return logger


#Separador Visual nos Logs 
def log_separador(titulo: str = ""):
    """Imprime um separador visual no log para marcar fases da execução."""
    linha = "─" * 55
    if titulo:
        logging.info(linha)
        logging.info(f"  {titulo.upper()}")
        logging.info(linha)
    else:
        logging.info(linha)


#Resumo Final nos Logs 
def log_resumo(total_urls: int, total_scraping: int, total_relevantes: int):
    """Regista um resumo da execução no final do log."""
    log_separador("resumo da execução")
    logging.info(f"  URLs descobertos      : {total_urls}")
    logging.info(f"  Artigos extraídos     : {total_scraping}")
    logging.info(f"  Artigos relevantes    : {total_relevantes}")
    logging.info(f"  Taxa de relevância    : "
                 f"{(total_relevantes/total_scraping*100):.1f}%"
                 if total_scraping > 0 else "  Taxa de relevância    : N/A")
    log_separador()


#Teste Direto 
if __name__ == "__main__":
    configurar_logger(nivel_consola="DEBUG", nivel_ficheiro="DEBUG")

    log_separador("teste do sistema de logging")

    logging.debug   ("Mensagem de DEBUG    — detalhe máximo")
    logging.info    ("Mensagem de INFO     — fluxo normal")
    logging.warning ("Mensagem de WARNING  — algo inesperado")
    logging.error   ("Mensagem de ERROR    — falha numa operação")
    logging.critical("Mensagem de CRITICAL — falha crítica")

    log_resumo(total_urls=50, total_scraping=42, total_relevantes=18)

    print(f"\n Log guardado em: {LOG_FILE}")