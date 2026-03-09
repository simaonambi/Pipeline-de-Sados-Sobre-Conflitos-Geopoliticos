#  Monitor de Notícias de Conflitos Geopolíticos

Web Crawler + Scraper automático do jornal **Público** focado em notícias
de conflitos entre países que possam indicar uma escalada para a
**Terceira Guerra Mundial**.

Desenvolvido no âmbito do Lab 02 da UC de **Extração e Transformação de Dados**
— Inteligência Artificial e Ciência de Dados @ DI/UBI.

---

##  Descrição

O sistema recolhe automaticamente artigos do [Público](https://www.publico.pt),
analisa o seu conteúdo com um filtro de palavras-chave ponderadas e guarda
os artigos relevantes em **CSV**, **JSON** e **SQLite**.

Cada artigo recebe um **score de relevância (0-100)** baseado em:
- Keywords críticas: `guerra nuclear`, `terceira guerra`, `WWIII` → peso 3
- Keywords altas: `NATO`, `míssil`, `invasão`, `bombardeamento` → peso 2
- Keywords médias: `tensão`, `sanções`, `ciberataque`, `escalada` → peso 1
- Regiões em conflito: `Ucrânia`, `Taiwan`, `Gaza`, `Irão`, `Putin` → peso 1

---

##  Estrutura do Projeto
```
lab02/
├── main.py                   # Ponto de entrada — orquestra todos os módulos
├── crawler_publico.py        # Descobre links de artigos reais no Público
├── scraper.py                # Extrai dados de cada artigo (título, autor, data...)
├── filtro_geopolitico.py     # Filtra artigos por relevância geopolítica
├── storage.py                # Guarda dados em CSV e JSON
├── database.py               # Gere base de dados SQLite
├── logger_config.py          # Configuração de logging
├── requirements.txt          # Dependências externas
│
├── output/
│   ├── noticias_conflitos.csv
│   ├── noticias_conflitos.json
│   └── noticias_conflitos.db
│
└── logs/
    └── crawler_YYYYMMDD_HHMMSS.log
```

---

##  Instalação

### 1. Clonar o repositório
```bash
git clone https://github.com/[teu-username]/[nome-do-repo].git
cd [nome-do-repo]
```

### 2. Criar ambiente virtual
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

---

##  Execução
```bash
python main.py
```

O programa executa automaticamente as 4 fases:
```
FASE 1 — Crawling       → descobre URLs de artigos no Público
FASE 2 — Scraping       → extrai dados de cada artigo
FASE 3 — Filtro         → analisa relevância geopolítica
FASE 4 — Armazenamento  → guarda em CSV, JSON e SQLite
```

No final mostra as estatísticas no terminal:
```
═══════════════════════════════════════════════════════
   ESTATÍSTICAS — NOTÍCIAS DE CONFLITO RECOLHIDAS
═══════════════════════════════════════════════════════
  Total de artigos relevantes : 10
  Score médio de relevância   : 5.3/100
  Score máximo                : 9/100

   Por categoria:
     mundo                → 7 artigos
     politica             → 2 artigos
     economia             → 1 artigo

   Top 5 keywords mais frequentes:
     'guerra'      →  4x
     'petróleo'    →  3x
     'irão'        →  2x

   Top 3 artigos mais relevantes:
     1. [9/100] Guerra no Médio Oriente: preço do petróleo dispara 25%
     2. [9/100] Trump mandou Pedro Sánchez sentar-se — vídeo é falso
     3. [8/100] Japão instala míssil de longo alcance desenvolvido no país
═══════════════════════════════════════════════════════
```

---

##  Dependências

| Biblioteca | Versão | Uso |
|---|---|---|
| `requests` | 2.31.0 | Requisições HTTP |
| `beautifulsoup4` | 4.12.3 | Parsing HTML |
| `lxml` | 5.1.0 | Parser HTML rápido |
| `sqlite3` | nativa | Base de dados (built-in) |
| `logging` | nativa | Sistema de logs (built-in) |

---

## 🗄️ Dados Gerados

### CSV — `output/noticias_conflitos.csv`
| Campo | Descrição |
|---|---|
| `titulo` | Título do artigo |
| `subtitulo` | Lead / subtítulo |
| `autor` | Nome do jornalista |
| `data_publicacao` | Data ISO 8601 |
| `categoria` | Secção (mundo, politica, economia) |
| `resumo` | Primeiros parágrafos |
| `link` | URL do artigo |
| `keywords_encontradas` | Keywords detetadas |
| `score_relevancia` | Score 0-100 |
| `data_recolha` | Timestamp de recolha |

### Base de Dados SQLite — `output/noticias_conflitos.db`
- **`artigos`** — dados principais com constraint `UNIQUE` no link
- **`keywords`** — relação 1:N com artigos
- **`execucoes`** — registo de cada execução do crawler

---

##  Boas Práticas

-  Verifica `robots.txt` antes de aceder a qualquer URL
-  Pausa de 1.5s entre pedidos (rate limiting)
-  Identifica o crawler no `User-Agent`
-  Recolhe apenas artigos de acesso público
-  Evita duplicados entre execuções
-  Regista todos os erros em ficheiro de log

---

##  Seeds (secções monitorizadas)
```python
SEED_URLS = [
    "https://www.publico.pt/mundo",
    "https://www.publico.pt/politica",
    "https://www.publico.pt/economia",
]
```

---

##  Licença

Projeto académico — UC Extração e Transformação de Dados  
DI @ Universidade da Beira Interior — 2025/2026
