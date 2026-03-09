"""
scraper.py
Responsável por:
- Aceder a cada URL da fila
- Extrair os campos do artigo (título, autor, data, etc.)
- Validar e limpar os dados extraídos
"""

import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import time

# ─── Configuração Base 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Lab02Crawler/1.0; UBI-ETD)"
}

DELAY_SECONDS = 1.5


# ─── Extração de Título
def extrair_titulo(soup: BeautifulSoup) -> str | None:
    """
    Tenta extrair o título real do artigo por ordem de prioridade:
    1. h1 com classe relacionada com headline/title/article
    2. Qualquer h1 que não seja apenas 'PÚBLICO'
    3. Meta tag og:title (remove sufixo ' | PÚBLICO')
    """
    # 1. h1 com classes específicas do Público
    for classe in ["headline", "title", "article", "story"]:
        el = soup.find("h1", class_=lambda c: c and classe in str(c).lower())
        if el:
            texto = el.get_text(strip=True)
            if texto and texto.upper() != "PÚBLICO":
                return texto

    # 2. Qualquer h1 válido
    h1 = soup.find("h1")
    if h1:
        texto = h1.get_text(strip=True)
        if texto and texto.upper() != "PÚBLICO":
            return texto

    # 3. Fallback: meta og:title
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return og["content"].replace(" | PÚBLICO", "").strip()

    return None


# ─── Extração de Subtítulo 
def extrair_subtitulo(soup: BeautifulSoup) -> str | None:
    """Extrai o subtítulo/lead do artigo."""
    # Meta og:description é geralmente o lead no Público
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        return og_desc["content"].strip()

    # Fallback: parágrafo com classe lead
    lead = soup.find("p", class_=lambda c: c and "lead" in str(c).lower())
    if lead:
        return lead.get_text(strip=True)

    # Fallback: h2
    h2 = soup.find("h2")
    if h2:
        return h2.get_text(strip=True)

    return None


# ─── Extração de Autor
def extrair_autor(soup: BeautifulSoup) -> str:
    """Extrai o nome do autor do artigo."""
    # rel=author é o mais fiável
    autor_tag = soup.find("a", rel="author")
    if autor_tag:
        return autor_tag.get_text(strip=True)

    # Classe com 'author' ou 'autor'
    for classe in ["author", "autor", "byline"]:
        el = soup.find(class_=lambda c: c and classe in str(c).lower())
        if el:
            texto = el.get_text(strip=True)
            if texto:
                return texto

    # Meta tag author
    meta_author = soup.find("meta", attrs={"name": "author"})
    if meta_author and meta_author.get("content"):
        return meta_author["content"].strip()

    return "Redação"


# ─── Extração de Data
def extrair_data(soup: BeautifulSoup) -> str:
    """Extrai a data de publicação do artigo."""
    # Tag <time> com atributo datetime
    time_tag = soup.find("time")
    if time_tag:
        return time_tag.get("datetime") or time_tag.get_text(strip=True)

    # Meta tag article:published_time
    meta_date = soup.find("meta", property="article:published_time")
    if meta_date and meta_date.get("content"):
        return meta_date["content"].strip()

    return ""


# ─── Extração de Resumo
def extrair_resumo(soup: BeautifulSoup) -> str:
    """
    Extrai os primeiros parágrafos úteis do corpo do artigo.
    Filtra parágrafos curtos ou de navegação.
    """
    paragrafos = soup.find_all("p")
    uteis = [
        p.get_text(strip=True)
        for p in paragrafos
        if len(p.get_text(strip=True)) > 40
    ]
    resumo = " ".join(uteis[:3])
    resumo = resumo.replace("\n", " ").replace("\r", "").strip()
    return resumo[:500] + "..." if len(resumo) > 500 else resumo


# ─── Extração de Categoria 
def extrair_categoria(url: str) -> str:
    """
    Extrai a categoria a partir do padrão de URL do Público:
    /YYYY/MM/DD/categoria/tipo/titulo
     [0]  [1] [2]   [3]   [4]   [5]
    """
    path_parts = urlparse(url).path.strip("/").split("/")
    # índice 3 é a categoria (mundo, politica, economia, etc.)
    if len(path_parts) >= 4 and path_parts[0].isdigit():
        return path_parts[3]
    return "desconhecida"


# ─── Scraping de Artigo 
def scrape_article(url: str) -> dict | None:
    """
    Acede a um artigo do Público e extrai todos os campos relevantes.
    Retorna dicionário com os dados ou None se falhar.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # ── Extrair cada campo
        titulo    = extrair_titulo(soup)
        subtitulo = extrair_subtitulo(soup)
        autor     = extrair_autor(soup)
        data      = extrair_data(soup)
        categoria = extrair_categoria(url)
        resumo    = extrair_resumo(soup)

        # ── Validação obrigatória 
        if not titulo:
            logging.warning(f"[Scraper] Sem título, artigo ignorado: {url}")
            return None

        artigo = {
            "titulo":               titulo,
            "subtitulo":            subtitulo or "",
            "autor":                autor,
            "data_publicacao":      data,
            "categoria":            categoria,
            "resumo":               resumo,
            "link":                 url,
            "keywords_encontradas": "",   # preenchido pelo filtro_geopolitico.py
            "score_relevancia":     0,    # preenchido pelo filtro_geopolitico.py
            "data_recolha":         datetime.now().isoformat(),
        }

        logging.info(f"[Scraper] ✓ Extraído: {titulo[:60]}...")
        return artigo

    except requests.exceptions.HTTPError as e:
        logging.error(f"[Scraper] HTTP {e.response.status_code} em {url}")
    except requests.exceptions.Timeout:
        logging.error(f"[Scraper] Timeout em {url}")
    except requests.exceptions.ConnectionError:
        logging.error(f"[Scraper] Sem ligação para {url}")
    except AttributeError as e:
        logging.error(f"[Scraper] Erro de parsing em {url}: {e}")
    except Exception as e:
        logging.error(f"[Scraper] Erro inesperado em {url}: {e}")

    return None


# ─── Processar Lista de URLs ──────────────────────────────────────────────────
def scrape_all(urls: list) -> list:
    """
    Percorre a lista de URLs e extrai dados de cada artigo.
    Retorna lista de dicionários com os artigos extraídos.
    """
    artigos = []

    for i, url in enumerate(urls, start=1):
        logging.info(f"[Scraper] A processar {i}/{len(urls)}: {url}")
        artigo = scrape_article(url)

        if artigo:
            artigos.append(artigo)

        time.sleep(DELAY_SECONDS)

    logging.info(
        f"[Scraper] Concluído: {len(artigos)} artigos extraídos "
        f"de {len(urls)} URLs"
    )
    return artigos


# ─── Teste Direto 
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    url_teste = "https://www.publico.pt/2026/03/09/mundo/noticia/hrw-acusa-israel-voltar-usar-fosforo-branco-alvos-civis-libano-2167284"
    print(f"A testar scraping em:\n{url_teste}\n")

    resultado = scrape_article(url_teste)

    if resultado:
        for campo, valor in resultado.items():
            print(f"  {campo:<25}: {str(valor)[:80]}")
    else:
        print("Nenhum dado extraído.")