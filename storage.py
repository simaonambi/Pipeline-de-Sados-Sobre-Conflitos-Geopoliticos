"""
storage.py
Responsável por:
- Guardar artigos filtrados em CSV e JSON
- Carregar dados já existentes (evita duplicados)
- Mostrar estatísticas resumidas dos dados recolhidos
"""

import csv
import json
import os
import logging
from datetime import datetime

# ─── Configuração de Paths ────────────────────────────────────────────────────
OUTPUT_DIR  = "output"
CSV_FILE    = os.path.join(OUTPUT_DIR, "noticias_conflitos.csv")
JSON_FILE   = os.path.join(OUTPUT_DIR, "noticias_conflitos.json")

CAMPOS_CSV = [
    "titulo",
    "subtitulo",
    "autor",
    "data_publicacao",
    "categoria",
    "resumo",
    "link",
    "keywords_encontradas",
    "score_relevancia",
    "data_recolha",
]


# ─── Criar Diretório de Output ────────────────────────────────────────────────
def garantir_output_dir():
    """Cria o diretório output/ se não existir."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logging.info(f"[Storage] Diretório criado: {OUTPUT_DIR}/")


# ─── Carregar Dados Existentes ────────────────────────────────────────────────
def carregar_links_existentes() -> set:
    """
    Lê o CSV existente e retorna um set com os links já guardados.
    Usado para evitar duplicados em execuções seguintes.
    """
    links = set()
    if os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("link"):
                        links.add(row["link"])
            logging.info(f"[Storage] {len(links)} links já existentes carregados")
        except Exception as e:
            logging.error(f"[Storage] Erro ao carregar CSV existente: {e}")
    return links


# ─── Guardar em CSV ───────────────────────────────────────────────────────────
def guardar_csv(artigos: list) -> int:
    """
    Acrescenta artigos novos ao CSV (append).
    Não sobrescreve dados anteriores.
    Retorna o número de artigos efetivamente guardados.
    """
    garantir_output_dir()

    if not artigos:
        logging.warning("[Storage] Nenhum artigo para guardar em CSV.")
        return 0

    # Verificar se ficheiro já existe para decidir se escreve header
    ficheiro_novo = not os.path.exists(CSV_FILE)

    guardados = 0
    try:
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CAMPOS_CSV, extrasaction="ignore")

            if ficheiro_novo:
                writer.writeheader()

            for artigo in artigos:
                writer.writerow(artigo)
                guardados += 1

        logging.info(f"[Storage] {guardados} artigos guardados em {CSV_FILE}")

    except PermissionError:
        logging.error(f"[Storage] Sem permissão para escrever em {CSV_FILE}")
    except Exception as e:
        logging.error(f"[Storage] Erro ao guardar CSV: {e}")

    return guardados


# ─── Guardar em JSON ──────────────────────────────────────────────────────────
def guardar_json(artigos: list) -> int:
    """
    Acrescenta artigos novos ao JSON existente.
    Carrega dados anteriores, faz merge e reescreve o ficheiro.
    Retorna o número de artigos no ficheiro final.
    """
    garantir_output_dir()

    if not artigos:
        logging.warning("[Storage] Nenhum artigo para guardar em JSON.")
        return 0

    # Carregar dados anteriores se existirem
    dados_existentes = []
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                dados_existentes = json.load(f)
        except json.JSONDecodeError:
            logging.warning("[Storage] JSON existente corrompido, será substituído.")
        except Exception as e:
            logging.error(f"[Storage] Erro ao carregar JSON: {e}")

    # Merge evitando duplicados por link
    links_existentes = {a["link"] for a in dados_existentes}
    novos = [a for a in artigos if a["link"] not in links_existentes]
    dados_finais = dados_existentes + novos

    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(dados_finais, f, ensure_ascii=False, indent=2)

        logging.info(
            f"[Storage] JSON atualizado: {len(novos)} novos + "
            f"{len(dados_existentes)} anteriores = {len(dados_finais)} total"
        )

    except Exception as e:
        logging.error(f"[Storage] Erro ao guardar JSON: {e}")

    return len(dados_finais)


#Estatísticas 
def mostrar_estatisticas(artigos: list):
    """
    Imprime um resumo estatístico dos artigos recolhidos.
    """
    if not artigos:
        print("\n[Storage] Sem artigos para analisar.")
        return

    scores = [a["score_relevancia"] for a in artigos]

    # Contagem por categoria
    categorias = {}
    for a in artigos:
        cat = a.get("categoria", "desconhecida")
        categorias[cat] = categorias.get(cat, 0) + 1

    # Top 5 keywords
    todas_keywords = []
    for a in artigos:
        kws = a.get("keywords_encontradas", "")
        if kws:
            todas_keywords.extend([k.strip() for k in kws.split(",")])

    contagem_kw = {}
    for kw in todas_keywords:
        contagem_kw[kw] = contagem_kw.get(kw, 0) + 1
    top_keywords = sorted(contagem_kw.items(), key=lambda x: x[1], reverse=True)[:5]

    print("\n" + "═" * 55)
    print("   ESTATÍSTICAS — NOTÍCIAS DE CONFLITO RECOLHIDAS")
    print("═" * 55)
    print(f"  Total de artigos relevantes : {len(artigos)}")
    print(f"  Score médio de relevância   : {sum(scores)/len(scores):.1f}/100")
    print(f"  Score máximo                : {max(scores)}/100")
    print(f"  Score mínimo                : {min(scores)}/100")

    print("\n   Por categoria:")
    for cat, count in sorted(categorias.items(), key=lambda x: x[1], reverse=True):
        print(f"     {cat:<20} → {count} artigos")

    print("\n   Top 5 keywords mais frequentes:")
    for kw, count in top_keywords:
        print(f"     '{kw}'  →  {count}x")

    print("\n   Top 3 artigos mais relevantes:")
    for i, a in enumerate(artigos[:3], 1):
        print(f"     {i}. [{a['score_relevancia']}/100] {a['titulo'][:55]}...")

    print("═" * 55 + "\n")


#  Teste Direto 
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    # Dados de teste
    artigos_teste = [
        {
            "titulo": "Rússia lança ataque com mísseis à Ucrânia durante a noite",
            "subtitulo": "NATO reúne de urgência após bombardeamento em Kiev",
            "autor": "Redação",
            "data_publicacao": "2026-03-09T08:00:00",
            "categoria": "mundo",
            "resumo": "Forças russas lançaram uma vaga de mísseis e drones...",
            "link": "https://publico.pt/mundo/noticia/russia-ataque-ucrania-1",
            "keywords_encontradas": "bombardeamento, míssil, nato, rússia, ucrânia",
            "score_relevancia": 87,
            "data_recolha": datetime.now().isoformat(),
        },
        {
            "titulo": "China aumenta pressão militar sobre Taiwan",
            "subtitulo": "Porta-aviões chinês entra na zona de exclusão",
            "autor": "João Silva",
            "data_publicacao": "2026-03-09T10:00:00",
            "categoria": "mundo",
            "resumo": "Tensões no Indo-Pacífico escalam com novas manobras...",
            "link": "https://publico.pt/mundo/noticia/china-taiwan-pressao-2",
            "keywords_encontradas": "china, porta-aviões, taiwan, tensões",
            "score_relevancia": 72,
            "data_recolha": datetime.now().isoformat(),
        },
    ]

    guardar_csv(artigos_teste)
    guardar_json(artigos_teste)
    mostrar_estatisticas(artigos_teste)