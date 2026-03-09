"""
filtro_geopolitico.py
Responsável por:
- Analisar cada artigo extraído pelo scraper
- Detetar keywords relacionadas com conflitos / WWIII
- Calcular score de relevância (0-100)
- Descartar artigos não relevantes
"""

import re
import logging

# ─── Dicionário de Keywords por Peso
KEYWORDS = {
    "critico": {
        "peso": 3,
        "termos": [
            "terceira guerra", "terceira guerra mundial", "wwiii", "world war iii",
            "guerra nuclear", "ataque nuclear", "bomba nuclear", "ogiva nuclear",
            "armas nucleares", "conflito nuclear", "holocausto nuclear",
            "armas de destruição", "guerra mundial",
        ]
    },
    "alto": {
        "peso": 2,
        "termos": [
            "invasão", "ataque militar", "bombardeamento", "bombardeio",
            "míssil", "missil", "drone militar", "ataque com drones",
            "nato", "otan", "conflito armado", "guerra", "ofensiva militar",
            "tropas", "exército", "forças armadas", "tanques", "artilharia",
            "porta-aviões", "submarino nuclear", "aliança militar",
            "declaração de guerra", "estado de guerra", "mobilização militar",
            "fosforo branco", "fósforo branco", "hackers russos",
            "ataque irao", "ataque irão",
        ]
    },
    "medio": {
        "peso": 1,
        "termos": [
            "tensão", "tensões", "sanções", "sanção", "embargo",
            "diplomacia", "crise diplomática", "ultimato", "negociações de paz",
            "fronteira", "território disputado", "anexação", "ocupação",
            "aliança", "tratado", "acordo de paz", "cessar-fogo", "armistício",
            "provocação", "escalada", "confronto", "incidente",
            "espionagem", "ciber-ataque", "ciberataque", "guerra híbrida",
            "refugiados de guerra", "zona de conflito", "área de conflito",
            "petróleo", "petroleo", "precio petroleo", "preco petroleo",
            "longo alcance", "míssil balístico", "missil balistico",
            "instala missil", "instala míssil",
        ]
    }
}

# ─── Países / Regiões em Conflito Ativo
REGIOES_CONFLITO = [
    # Europa de Leste
    "ucrânia", "ucrania", "rússia", "russia", "kremlin", "kiev", "kyiv",
    "moscovo", "moscou", "donbass", "zaporizhzhia", "kherson",
    # Médio Oriente
    "israel", "palestina", "gaza", "hamas", "hezbollah", "líbano", "libano",
    "irão", "irao", "iran", "síria", "siria", "iémen", "iemen", "yemen",
    # Ásia
    "taiwan", "china", "coreia do norte", "coreia", "mar do sul da china",
    "indo-pacífico", "indopacífico", "japao", "japão",
    # Outros
    "sudão", "sudao", "etiópia", "etiopia", "sahel", "mali", "níger", "niger",
    # Grandes potências em conflito
    "trump", "putin", "xi jinping", "kim jong",
]

# ─── Score Mínimo 
# Baixado para 2 para capturar artigos cujo resumo ainda é curto
SCORE_MINIMO = 2


# ─── Normalização de Texto 
def normalizar(texto: str) -> str:
    """Converte para minúsculas e remove pontuação extra."""
    texto = texto.lower()
    texto = re.sub(r"[^\w\sáéíóúâêîôûãõàèìòùçü\-]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


# ─── Análise de Relevância 
def analisar_relevancia(artigo: dict) -> dict:
    """
    Analisa um artigo e calcula o score de relevância geopolítica.
    O título é analisado com peso triplo por ser o campo mais fiável.
    """
    # Título repetido 3x para ter maior peso na análise
    titulo     = artigo.get("titulo", "")
    subtitulo  = artigo.get("subtitulo", "")
    resumo     = artigo.get("resumo", "")

    # Também analisa o URL — contém palavras-chave do tema do artigo
    link       = artigo.get("link", "").replace("-", " ").replace("/", " ")

    texto_completo = " ".join([
        titulo, titulo, titulo,   # título com peso triplo
        subtitulo,
        resumo,
        link,                     # URL também analisado
    ])
    texto_norm = normalizar(texto_completo)

    score = 0
    keywords_encontradas = []

    # ── Verificar Keywords por Categoria 
    for categoria, dados in KEYWORDS.items():
        for termo in dados["termos"]:
            if termo in texto_norm:
                score += dados["peso"]
                keywords_encontradas.append(termo)

    # ── Verificar Regiões de Conflito 
    for regiao in REGIOES_CONFLITO:
        if regiao in texto_norm:
            score += 1
            keywords_encontradas.append(regiao)

    # ── Normalizar Score para 0-100
    score_normalizado = min(round((score / 80) * 100), 100)

    # ── Filtrar por Score Mínimo 
    if score_normalizado < SCORE_MINIMO:
        logging.info(
            f"[Filtro] ✗ Descartado (score={score_normalizado}): "
            f"{artigo.get('titulo', '')[:50]}..."
        )
        return None

    # ── Atualizar Artigo 
    artigo["keywords_encontradas"] = ", ".join(sorted(set(keywords_encontradas)))
    artigo["score_relevancia"]     = score_normalizado

    logging.info(
        f"[Filtro] ✓ Relevante (score={score_normalizado}): "
        f"{artigo.get('titulo', '')[:50]}..."
    )
    return artigo


# ─── Filtrar Lista de Artigos 
def filtrar_artigos(artigos: list) -> list:
    """
    Recebe lista de artigos e retorna apenas os relevantes,
    ordenados por score decrescente.
    """
    relevantes = []

    for artigo in artigos:
        resultado = analisar_relevancia(artigo)
        if resultado:
            relevantes.append(resultado)

    relevantes.sort(key=lambda x: x["score_relevancia"], reverse=True)

    logging.info(
        f"[Filtro] {len(relevantes)} artigos relevantes "
        f"de {len(artigos)} analisados"
    )
    return relevantes


# ─── Teste Direto 
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    testes = [
        {
            "titulo": "HRW acusa Israel de voltar a usar fósforo branco em alvos civis no Líbano",
            "subtitulo": "Organização diz ter provas de uso de arma incendiária",
            "resumo": "A Human Rights Watch acusou Israel de usar fósforo branco...",
            "categoria": "mundo",
            "link": "https://www.publico.pt/2026/03/09/mundo/noticia/hrw-acusa-israel-fosforo-branco-libano",
            "autor": "Redação",
            "data_publicacao": "",
            "keywords_encontradas": "",
            "score_relevancia": 0,
            "data_recolha": "",
        },
        {
            "titulo": "Japão instala míssil de longo alcance desenvolvido no país",
            "subtitulo": "Medida surge no contexto de tensões na região",
            "resumo": "O Japão instalou o seu primeiro míssil de longo alcance...",
            "categoria": "mundo",
            "link": "https://www.publico.pt/2026/03/09/mundo/noticia/japao-instala-missil-longo-alcance",
            "autor": "Redação",
            "data_publicacao": "",
            "keywords_encontradas": "",
            "score_relevancia": 0,
            "data_recolha": "",
        },
        {
            "titulo": "Festival de música em Lisboa bate recorde",
            "subtitulo": "Mais de 50 mil pessoas no evento",
            "resumo": "O festival decorreu sem incidentes no Parque das Nações...",
            "categoria": "cultura",
            "link": "https://www.publico.pt/2026/03/09/cultura/noticia/festival-lisboa",
            "autor": "Redação",
            "data_publicacao": "",
            "keywords_encontradas": "",
            "score_relevancia": 0,
            "data_recolha": "",
        },
    ]

    resultados = filtrar_artigos(testes)

    print(f"\n {len(resultados)} artigos relevantes:\n")
    for a in resultados:
        print(f"  [{a['score_relevancia']:>3}/100] {a['titulo']}")
        print(f"           Keywords: {a['keywords_encontradas']}\n")