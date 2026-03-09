"""
database.py
Responsável por:
- Criar e gerir a base de dados SQLite
- Inserir artigos evitando duplicados
- Consultar artigos por score, keyword ou data
- Mostrar estatísticas da base de dados
"""

import sqlite3
import logging
import os
from datetime import datetime

#  Configuração
DB_DIR  = "output"
DB_FILE = os.path.join(DB_DIR, "noticias_conflitos.db")


# ─── Ligação à Base de Dados
def get_connection() -> sqlite3.Connection:
    """Cria e retorna uma ligação à base de dados SQLite."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # permite aceder por nome de coluna
    return conn


# ─── Criar Tabelas 
def criar_tabelas():
    """
    Cria as tabelas necessárias se ainda não existirem.

    Tabelas:
      - artigos        : dados principais de cada notícia
      - keywords       : keywords encontradas por artigo (relação 1:N)
      - execucoes      : registo de cada execução do crawler
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Tabela principal de artigos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artigos (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo           TEXT    NOT NULL,
                subtitulo        TEXT,
                autor            TEXT,
                data_publicacao  TEXT,
                categoria        TEXT,
                resumo           TEXT,
                link             TEXT    UNIQUE NOT NULL,
                score_relevancia INTEGER DEFAULT 0,
                data_recolha     TEXT,
                criado_em        TEXT    DEFAULT (datetime('now'))
            )
        """)

        # Tabela de keywords (relação N:1 com artigos)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                artigo_id INTEGER NOT NULL,
                keyword   TEXT    NOT NULL,
                FOREIGN KEY (artigo_id) REFERENCES artigos(id) ON DELETE CASCADE
            )
        """)

        # Tabela de registo de execuções
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execucoes (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                data_execucao     TEXT    DEFAULT (datetime('now')),
                total_urls        INTEGER DEFAULT 0,
                total_extraidos   INTEGER DEFAULT 0,
                total_relevantes  INTEGER DEFAULT 0
            )
        """)

        # Índices para queries mais rápidas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_score ON artigos(score_relevancia)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_data  ON artigos(data_publicacao)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kw    ON keywords(keyword)")

        conn.commit()
        logging.info(f"[DB] Tabelas criadas/verificadas em: {DB_FILE}")

    except sqlite3.Error as e:
        logging.error(f"[DB] Erro ao criar tabelas: {e}")
    finally:
        conn.close()


# ─── Inserir Artigos 
def inserir_artigos(artigos: list) -> int:
    """
    Insere lista de artigos na base de dados.
    Ignora artigos cujo link já existe (UNIQUE constraint).
    Retorna o número de artigos efetivamente inseridos.
    """
    if not artigos:
        logging.warning("[DB] Nenhum artigo para inserir.")
        return 0

    conn = get_connection()
    inseridos = 0

    try:
        cursor = conn.cursor()

        for artigo in artigos:
            try:
                # Inserir artigo principal
                cursor.execute("""
                    INSERT INTO artigos
                        (titulo, subtitulo, autor, data_publicacao,
                         categoria, resumo, link, score_relevancia, data_recolha)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    artigo.get("titulo"),
                    artigo.get("subtitulo"),
                    artigo.get("autor"),
                    artigo.get("data_publicacao"),
                    artigo.get("categoria"),
                    artigo.get("resumo"),
                    artigo.get("link"),
                    artigo.get("score_relevancia", 0),
                    artigo.get("data_recolha"),
                ))

                artigo_id = cursor.lastrowid

                # Inserir keywords associadas
                keywords_raw = artigo.get("keywords_encontradas", "")
                if keywords_raw:
                    keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
                    for kw in keywords:
                        cursor.execute("""
                            INSERT INTO keywords (artigo_id, keyword)
                            VALUES (?, ?)
                        """, (artigo_id, kw))

                inseridos += 1
                logging.debug(f"[DB] Inserido: {artigo.get('titulo', '')[:50]}...")

            except sqlite3.IntegrityError:
                # Link duplicado — ignorar silenciosamente
                logging.debug(f"[DB] Duplicado ignorado: {artigo.get('link')}")

        conn.commit()
        logging.info(f"[DB] {inseridos} artigos inseridos na base de dados")

    except sqlite3.Error as e:
        logging.error(f"[DB] Erro ao inserir artigos: {e}")
        conn.rollback()
    finally:
        conn.close()

    return inseridos


# ─── Registar Execução 
def registar_execucao(total_urls: int, total_extraidos: int, total_relevantes: int):
    """Regista os resultados de uma execução na tabela execucoes."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO execucoes (total_urls, total_extraidos, total_relevantes)
            VALUES (?, ?, ?)
        """, (total_urls, total_extraidos, total_relevantes))
        conn.commit()
        logging.info("[DB] Execução registada.")
    except sqlite3.Error as e:
        logging.error(f"[DB] Erro ao registar execução: {e}")
    finally:
        conn.close()


# ─── Consultas 
def consultar_por_score(score_minimo: int = 70) -> list:
    """Retorna artigos com score acima do mínimo, ordenados por score."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT titulo, autor, data_publicacao, categoria,
                   score_relevancia, link
            FROM artigos
            WHERE score_relevancia >= ?
            ORDER BY score_relevancia DESC
        """, (score_minimo,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"[DB] Erro na consulta por score: {e}")
        return []
    finally:
        conn.close()


def consultar_por_keyword(keyword: str) -> list:
    """Retorna artigos que contêm uma keyword específica."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT DISTINCT a.titulo, a.autor, a.data_publicacao,
                            a.score_relevancia, a.link
            FROM artigos a
            JOIN keywords k ON a.id = k.artigo_id
            WHERE k.keyword LIKE ?
            ORDER BY a.score_relevancia DESC
        """, (f"%{keyword}%",))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"[DB] Erro na consulta por keyword: {e}")
        return []
    finally:
        conn.close()


def consultar_recentes(limite: int = 10) -> list:
    """Retorna os artigos mais recentes."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT titulo, autor, data_publicacao, score_relevancia, link
            FROM artigos
            ORDER BY data_recolha DESC
            LIMIT ?
        """, (limite,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"[DB] Erro na consulta de recentes: {e}")
        return []
    finally:
        conn.close()


# ─── Estatísticas da BD 
def estatisticas_db():
    """Imprime estatísticas gerais da base de dados."""
    conn = get_connection()
    try:
        total     = conn.execute("SELECT COUNT(*) FROM artigos").fetchone()[0]
        score_med = conn.execute("SELECT AVG(score_relevancia) FROM artigos").fetchone()[0]
        score_max = conn.execute("SELECT MAX(score_relevancia) FROM artigos").fetchone()[0]
        execucoes = conn.execute("SELECT COUNT(*) FROM execucoes").fetchone()[0]

        # Top 5 keywords
        top_kw = conn.execute("""
            SELECT keyword, COUNT(*) as total
            FROM keywords
            GROUP BY keyword
            ORDER BY total DESC
            LIMIT 5
        """).fetchall()

        print("\n" + "═" * 55)
        print("    ESTATÍSTICAS DA BASE DE DADOS SQLite")
        print("═" * 55)
        print(f"  Total de artigos       : {total}")
        print(f"  Score médio            : {score_med:.1f}/100" if score_med else "  Score médio: N/A")
        print(f"  Score máximo           : {score_max}/100")
        print(f"  Execuções registadas   : {execucoes}")
        print(f"  Ficheiro               : {DB_FILE}")
        print("\n   Top 5 keywords:")
        for row in top_kw:
            print(f"     '{row[0]}'  →  {row[1]}x")
        print("═" * 55 + "\n")

    except sqlite3.Error as e:
        logging.error(f"[DB] Erro nas estatísticas: {e}")
    finally:
        conn.close()


# ─── Teste Direto 
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    criar_tabelas()

    # Dados de teste
    artigos_teste = [
        {
            "titulo": "Rússia lança mísseis sobre Kiev",
            "subtitulo": "NATO reúne de urgência",
            "autor": "Ana Ferreira",
            "data_publicacao": "2026-03-09T03:15:00",
            "categoria": "mundo",
            "resumo": "Forças russas lançaram mísseis sobre a capital ucraniana...",
            "link": "https://publico.pt/mundo/russia-misseis-kiev",
            "keywords_encontradas": "míssil, nato, rússia, ucrânia, guerra",
            "score_relevancia": 87,
            "data_recolha": datetime.now().isoformat(),
        },
        {
            "titulo": "NATO ativa Artigo 5 pela primeira vez",
            "subtitulo": "Aliança declara ataque coletivo",
            "autor": "Rita Santos",
            "data_publicacao": "2026-03-03T20:00:00",
            "categoria": "mundo",
            "resumo": "A NATO ativou o Artigo 5 após ataque a país báltico...",
            "link": "https://publico.pt/mundo/nato-artigo5",
            "keywords_encontradas": "nato, terceira guerra, estado de guerra, rússia",
            "score_relevancia": 92,
            "data_recolha": datetime.now().isoformat(),
        },
    ]

    inserir_artigos(artigos_teste)
    registar_execucao(total_urls=50, total_extraidos=20, total_relevantes=2)
    estatisticas_db()

    print("Artigos com score >= 80:")
    for a in consultar_por_score(80):
        print(f"  [{a['score_relevancia']}/100] {a['titulo']}")

    print("\nArtigos com keyword 'nato':")
    for a in consultar_por_keyword("nato"):
        print(f"  [{a['score_relevancia']}/100] {a['titulo']}")