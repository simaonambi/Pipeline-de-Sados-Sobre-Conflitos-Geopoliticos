import logging
from logger_config      import configurar_logger, log_separador, log_resumo
from crawler_publico    import build_url_queue
from scraper            import scrape_all
from filtro_geopolitico import filtrar_artigos
from storage            import (
    carregar_links_existentes,
    guardar_csv,
    guardar_json,
    mostrar_estatisticas,
)

from database import criar_tabelas, inserir_artigos, registar_execucao


def main():

    # 1. Inicializar Logger
    configurar_logger(nivel_consola="INFO", nivel_ficheiro="DEBUG")
    log_separador("arranque do crawler — conflitos geopolíticos")
    logging.info("Fonte : publico.pt  |  Foco: conflitos / WWIII")

    # Inicializar Base de Dados
    criar_tabelas()

    # 2. Crawling
    log_separador("fase 1 — crawling")
    urls = build_url_queue()
    if not urls:
        logging.critical("Nenhum URL encontrado.")
        return

    # 3. Filtrar duplicados
    links_existentes = carregar_links_existentes()
    urls_novos = [u for u in urls if u not in links_existentes]
    if not urls_novos:
        logging.warning("Todos os URLs já foram processados.")
        return

    # 4. Scraping
    log_separador("fase 2 — scraping")
    artigos = scrape_all(urls_novos)
    if not artigos:
        logging.error("Nenhum artigo extraído.")
        return

    # 5. Filtro Geopolítico
    log_separador("fase 3 — filtro geopolítico")
    artigos_relevantes = filtrar_artigos(artigos)
    if not artigos_relevantes:
        logging.warning("Nenhum artigo passou o filtro.")
        return

    # 6. Storage
    log_separador("fase 4 — armazenamento")
    guardar_csv(artigos_relevantes)
    guardar_json(artigos_relevantes)

    # Base de Dados
    inserir_artigos(artigos_relevantes)
    registar_execucao(
        total_urls       = len(urls),
        total_extraidos  = len(artigos),
        total_relevantes = len(artigos_relevantes),
    )

    # 7. Estatísticas
    mostrar_estatisticas(artigos_relevantes)
    log_resumo(len(urls), len(artigos), len(artigos_relevantes))


if __name__ == "__main__":
    main()