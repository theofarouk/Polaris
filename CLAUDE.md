# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an OSINT (Open Source Intelligence) data collection system built with Docker Compose. The system consists of three main services:
- PostgreSQL database for data persistence
- Adminer web UI for database management
- Scrapy-based ingestion container that crawls and processes web content

## Architecture

### Core Components

- **Database Layer**: PostgreSQL with a `documents` table storing scraped content, metadata, and optional fields for embeddings and entity extraction
- **Ingestion Layer**: Python-based Scrapy framework with Trafilatura for content extraction
- **Web Interface**: Adminer for database inspection and queries

### Data Flow

1. Scrapy spider crawls sitemap.xml files to discover article URLs
2. Content is extracted using Trafilatura library 
3. PostgresPipeline stores data in database with deduplication (ON CONFLICT)
4. Database schema supports advanced features like embeddings and JSONB entities

## Development Commands

### Starting the System
```bash
docker compose up --build
```

### Running Individual Spiders
```bash
# Run brookings spider manually
docker compose run --rm ingestion scrapy crawl brookings -s LOG_LEVEL=INFO

# Run with different log levels
docker compose run --rm ingestion scrapy crawl brookings -s LOG_LEVEL=DEBUG
```

### Database Access
- **Adminer UI**: http://localhost:8080
  - System: PostgreSQL
  - Server: db  
  - User: osint
  - Password: secret
  - Database: geopolitics

### System Management
```bash
# Stop all services
docker compose down

# View logs for specific service
docker compose logs ingestion
docker compose logs db

# Rebuild specific service
docker compose build ingestion
```

## Code Structure

### Spider Development
- Spiders located in `ingestion/osint/spiders/`
- Each spider inherits from `scrapy.Spider`
- Use `looks_like_article()` helper to filter URLs
- Content extraction handled by Trafilatura with fallback parsing

### Database Schema
The `documents` table supports:
- Basic metadata (source, url, title, dates)
- Full-text content with SHA256 hashing
- Arrays for authors and tags
- JSONB for structured entities
- BYTEA for embeddings (future ML integration)

### Configuration
- Scrapy settings in `ingestion/osint/settings.py`
- Environment variables defined in `.env` file
- Database connection via PostgresPipeline

## Key Files

- `docker-compose.yml`: Service orchestration
- `db/init.sql`: Database schema initialization
- `ingestion/osint/pipelines.py`: Data processing and storage
- `ingestion/osint/spiders/brookings_spider.py`: Example spider implementation
- `ingestion/requirements.txt`: Python dependencies

## Environment Variables

Create `.env` file with:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `POSTGRES_PORT`, `TZ`

Default values are configured for development use.


## Project


Type : Veille stratégique et OSINT 

Objectif : **Scraping éthique** de bases de données de think tanks pour extraire des tendances régionales (traités, positionnements diplomatiques, sanctions)

Thinks Tanks = Brookings, IFRI, IISS

**Premier scraper** : Brookings (via sitemap ou RSS).  
→ Objectif : stocker 50–100 docs en base avec métadonnées + texte brut.

----

#### Roadmap

**S1–S2 (MVP ingestion)**
- Scrapers (RSS + 1 sitemap/source), stockage Postgres, extraction texte/PDF.  
**S3 (NLP v0)**
- NER FR/EN + règles; normalisation pays; index OpenSearch.  
**S4 (Tendances v1)**
- Agrégations, BERTopic, dashboard Metabase; alertes hebdos (“nouvelles sanctions mentionnées sur X”).  
**S5–S6 (Durcissement)**
- Tests, logs, quotas, doc; petit set d’exemples labellisés pour affiner la précision.

#### Architecture


# 1) Cadre éthique & légal (à respecter dès J0)

- **Respect des ToS & robots.txt** : pas de contournement de paywall, pas d’auth forcée. Delays + user‑agent clair, pas de paralélisation agressive.
    
- **Préférence API/RSS/sitemaps** quand disponibles (souvent + stable et + “propre” que le scraping HTML).
    
- **Minimisation** : ne collecter que le nécessaire (titre, URL, date, auteurs, résumé, texte).
    
- **Traçabilité** : stocker `source_url`, `retrieved_at`, `hash_contenu`, `robots_cache`.
    
- **Contact courtois** : si doute, mail type “research/fair use” (je te donne un modèle si tu veux).
    

# 2) Architecture simple et robuste

- **Ingestion** : Scrapy/Playwright + trafilatura/newspaper3k (extraction texte), RSS/sitemaps si dispos.
    
- **Parsing PDF** : GROBID (titres/auteurs), Apache Tika ou `pdfminer.six`.
    
- **File d’events** : SQLite/PostgreSQL au début; puis **Postgres** + **Timescale** si séries temporelles.
    
- **Recherche** : Elasticsearch/OpenSearch (ou Lite: Tantivy/Meili).
    
- **Orchestration** : Prefect/ Airflow (crons journaliers).
    
- **Conteneurisation** : Docker Compose (ingestion, NLP, base, kibana).
    
- **NLP** : spaCy (EN/FR), **sentence-transformers**, **BERTopic** pour thèmes; règles + NER pour traités/sanctions/positions.
    
- **Dashboard** : Kibana ou Metabase + un petit Streamlit pour filtres pays/sujets.
    

# 3) Schéma de données (MVP)

**Table `documents`**

- `id`, `source` (brookings/ifri/iiss), `url`, `title`, `date_published`, `date_collected`, `authors[]`, `language`, `section` (blog/report/brief)
    
- `content_text`, `content_html` (optionnel), `content_hash`
    
- `tags[]` (ex: “sanctions”, “treaty”, “statement”, régions/pays)
    
- `entities` (JSON: personnes, pays, orgs, traités)
    
- `embedding` (vecteur, optionnel)
    

**Table `events`** (sortie NLP normalisée)

- `doc_id`, `event_type` ∈ {`TREATY`,`SANCTION`,`POSITIONING`}
    
- `targets[]` (pays/acteurs), `policy_area` (défense, énergie, techno…), `stance` (pro/anti/nuancé), `confidence` (0–1)
    
- `date_event` (si détectable), `evidence_span` (offsets/quote)
    

# 4) Pipeline NLP (détection de tendances)

1. **Langue** : `langdetect` ou fastText.
    
2. **NER** (FR/EN) : spaCy `en_core_web_trf` + `fr_core_news_lg`. Normaliser pays/organisations via **Wikidata ISO‑3166**.
    
3. **Règles & classif** :
    
    - **Règles** (pattern mention + verbe d’action) pour évènements:
        
        - _SANCTION_ : “sanctions”, “embargo”, “listing/delisting”, “mesures restrictives”
            
        - _TREATY_ : “accord”, “traité”, “MoU”, “ratification”, “signature”
            
        - _POSITIONING_ : “condamne”, “soutient”, “exprime”, “appelle à”, “position”
            
    - **Classif supervisée** (optionnel) : petit modèle (logreg/SVM) entraîné sur ~300 exemples labellisés.
        
4. **Topic modeling** : **BERTopic** (ou LDA) pour thèmes émergents (ex: “mer Rouge”, “AUKUS”, “chips act”).
    
5. **Scoring confiance** : mélange heuristique (force du pattern, source, densité d’entités).
    
6. **Agrégation** : séries mensuelles par région/sujet + “top n clusters”.
    

# 5) Cibles & sources (pratiques)

- **Brookings** : blogs, reports, “Order from Chaos”, “Up Front”; privilégier RSS/sitemaps.
    
- **IFRI** : analyses, notes, podcasts; beaucoup de PDF → GROBID utile.
    
- **IISS** : The Strategist, reports, blogs; certains contenus sont members‑only → ne pas contourner.
    

# 6) Exemples de code (snippets rapides)

**Scrapy (respectueux) – RSS/sitemap si possible**

`# brookings_spider.py import scrapy, hashlib, datetime as dt from w3lib.html import remove_tags class BrookingsSpider(scrapy.Spider):     name = "brookings"     custom_settings = {"DOWNLOAD_DELAY": 1.5, "AUTOTHROTTLE_ENABLED": True}     start_urls = ["https://www.brookings.edu/sitemap_index.xml"]  # ou flux RSS spécifiques      def parse(self, resp):         for loc in resp.xpath("//loc/text()").getall():             if "sitemap-posts" in loc or loc.endswith(".xml"):                 yield scrapy.Request(loc, callback=self.parse_map)      def parse_map(self, resp):         for url in resp.xpath("//loc/text()").getall():             if url.endswith("/"):  # filtre simple                 yield scrapy.Request(url, callback=self.parse_article)      def parse_article(self, resp):         title = resp.css("h1::text").get() or resp.css("title::text").get()         date = resp.css("time::attr(datetime)").get()         text = " ".join(resp.css("article *::text").getall()).strip()         h = hashlib.sha256(text.encode("utf-8")).hexdigest()         yield {             "source": "brookings", "url": resp.url, "title": title,             "date_published": date, "date_collected": dt.datetime.utcnow().isoformat(),             "content_text": text, "content_hash": h         }`

**Extraction robuste de texte**

`import trafilatura downloaded = trafilatura.fetch_url(url) text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)`

**PDF → GROBID (titre/auteurs)**

`docker run -p 8070:8070 lfoppiano/grobid:0.7.3`

`import requests, json files = {'input': open('ifri_doc.pdf','rb')} r = requests.post("http://localhost:8070/api/processFulltextDocument", files=files) tei = r.text  # parser titre/auteurs/refs`

**NER & règles FR/EN**

`import spacy, re nlp_en = spacy.load("en_core_web_trf") nlp_fr = spacy.load("fr_core_news_lg")  def detect_events(text, lang="en"):     nlp = nlp_en if lang=="en" else nlp_fr     doc = nlp(text)     countries = [e.text for e in doc.ents if e.label_ in ("GPE","ORG")]     events = []     patterns = {         "SANCTION": r"\b(sanction(s)?|embargo|asset freeze|listing|mesures? restrictives?)\b",         "TREATY": r"\b(accord|trait[eé]|treat(y|ies)|MoU|ratifi\w+|signature)\b",         "POSITIONING": r"\b(condamne|soutient|oppose|urge|calls on|supports|deplor(e|a))\b",     }     lower = text.lower()     for etype, pat in patterns.items():         if re.search(pat, lower):             events.append({"event_type": etype, "targets": countries, "confidence": 0.6})     return events`

# 7) Tableau de bord (rapide)

- **Kibana/Metabase** pour :
    
    - Top sujets 30/90 jours
        
    - Carte des pays les plus mentionnés
        
    - Timeline “SANCTION vs TREATY vs POSITIONING”
        
- **Streamlit** (filtre par région / source / période) pour revue analyste + export CSV/PDF.
    

# 8) Roadmap 4–6 semaines

**S1–S2 (MVP ingestion)**

- Scrapers (RSS + 1 sitemap/source), stockage Postgres, extraction texte/PDF.  
    **S3 (NLP v0)**
    
- NER FR/EN + règles; normalisation pays; index OpenSearch.  
    **S4 (Tendances v1)**
    
- Agrégations, BERTopic, dashboard Metabase; alertes hebdos (“nouvelles sanctions mentionnées sur X”).  
    **S5–S6 (Durcissement)**
    
- Tests, logs, quotas, doc; petit set d’exemples labellisés pour affiner la précision.
    

# 9) Bonnes pratiques d’opérations

- **Auto‑throttle + backoff** en cas de 429/503.
    
- **Cache** des pages (hash → ne pas retraiter) + **diff** de contenu.
    
- **Monitoring** : taux d’erreurs, temps moyen par page, % PDFs.
    
- **Échantillonnage manuel** hebdo (qualité extraction & labels).


