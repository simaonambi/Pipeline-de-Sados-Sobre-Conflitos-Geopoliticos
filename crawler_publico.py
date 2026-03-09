"""
crawler_publico.py
Responsável por:
- Verificar robots.txt
- Descobrir links de artigos nas secções do Público
- Gerir a fila de URLs a visitar (evita duplicados)
"""

import requests
import logging
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import time

# ─── Configuração Base 
BASE_URL = "https://www.publico.pt"

SEED_URLS = [
    "https://www.publico.pt/mundo",
    "https://www.publico.pt/politica",
    "https://www.publico.pt/economia",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Lab02Crawler/1.0; UBI-ETD)"
}

MAX_ARTICLES  = 50
DELAY_SECONDS = 1.5


# ─── robots.txt 
def check_robots(url: str) -> bool:
    try:
        rp = RobotFileParser()
        rp.set_url(f"{BASE_URL}/robots.txt")
        rp.read()
        allowed = rp.can_fetch(HEADERS["User-Agent"], url)
        if not allowed:
            logging.warning(f"[robots.txt] Bloqueado: {url}")
        return allowed
    except Exception as e:
        logging.error(f"[robots.txt] Erro ao ler: {e}")
        return True


# ─── Extração de Links 
def get_article_links(section_url: str) -> list:
    """
    Extrai apenas links de artigos reais.
    URLs de artigos do Público seguem o padrão:
    /YYYY/MM/DD/secção/tipo/titulo-do-artigo-XXXXXXX
    ex: /2026/03/09/mundo/noticia/russia-ataca-kiev-2167289
    """
    links = []
    try:
        response = requests.get(section_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(BASE_URL, href)

            # Remove fragmentos (#comments, #section, etc.)
            full_url = full_url.split("#")[0]

            parsed = urlparse(full_url)
            partes = parsed.path.strip("/").split("/")

            if (
                parsed.netloc == "www.publico.pt"
                and len(partes) >= 4             # mínimo: ano/mes/dia/secção
                and partes[0].isdigit()          # começa com o ano ex: 2026
                and len(partes[0]) == 4          # confirma que é um ano de 4 dígitos
                and full_url not in links        # sem duplicados
            ):
                links.append(full_url)

        logging.info(f"[Crawler] {len(links)} links encontrados em: {section_url}")

    except requests.exceptions.HTTPError as e:
        logging.error(f"[Crawler] HTTP {e.response.status_code} em {section_url}")
    except requests.exceptions.ConnectionError:
        logging.error(f"[Crawler] Sem ligação para {section_url}")
    except requests.exceptions.Timeout:
        logging.error(f"[Crawler] Timeout em {section_url}")
    except Exception as e:
        logging.error(f"[Crawler] Erro inesperado em {section_url}: {e}")

    return links


# ─── Gestor da Fila de URLs 
def build_url_queue() -> list:
    """
    Percorre todas as SEED_URLS, recolhe links de artigos reais,
    remove duplicados e respeita robots.txt e MAX_ARTICLES.
    """
    fila     = []
    visitados = set()

    for seed in SEED_URLS:
        logging.info(f"[Crawler] A processar seed: {seed}")

        if not check_robots(seed):
            continue

        links = get_article_links(seed)

        for link in links:
            if link not in visitados and len(fila) < MAX_ARTICLES:
                if check_robots(link):
                    fila.append(link)
                    visitados.add(link)

        time.sleep(DELAY_SECONDS)

    logging.info(f"[Crawler] Fila final: {len(fila)} URLs para scraping")
    return fila


# ─── Teste Direto 
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    print("A construir fila de URLs...")
    urls = build_url_queue()

    print(f"\n Total de URLs recolhidos: {len(urls)}")
    print("\nPrimeiros 5:")
    for u in urls[:5]:
        print(f"  → {u}")