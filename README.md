# 🌍 OSINT Geopolitical Intelligence System

**Automated collection and analysis of geopolitical trends from think tank publications**

## 📋 Overview

This project implements an **ethical OSINT (Open Source Intelligence)** system for collecting and analyzing geopolitical content from major think tanks. It automatically detects diplomatic events like **sanctions**, **treaties**, and **political positions** using NLP techniques.

### 🎯 Key Features

- **Multi-source scraping**: Brookings (sitemap), IRIS, IFRI (RSS feeds)
- **NLP Analysis**: Automatic detection of geopolitical events using spaCy
- **Interactive Dashboard**: Real-time visualization with Streamlit
- **Docker Architecture**: Scalable microservices design
- **Ethical Approach**: Respects robots.txt, rate limiting, fair use

## 🏗️ Architecture

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Ingestion  │  │     NLP     │  │  Dashboard  │
│   (Scrapy)  │─▶│   (spaCy)   │─▶│ (Streamlit) │
└─────────────┘  └─────────────┘  └─────────────┘
        │               │               │
        └───────────────▼───────────────┘
              ┌─────────────────┐
              │   PostgreSQL    │
              │   + Adminer     │
              └─────────────────┘
```

### Services

- **`ingestion`**: Web scraping with Scrapy + Trafilatura
- **`nlp`**: Geopolitical event detection with spaCy  
- **`dashboard`**: Interactive visualization with Streamlit
- **`db`**: PostgreSQL database with dual schema
- **`adminer`**: Database web interface

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- 8GB+ RAM recommended (for spaCy models)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/osint-geopolitical-intel.git
   cd osint-geopolitical-intel
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (default values work for local development)
   ```

3. **Start the system**
   ```bash
   # Build all services
   docker compose build
   
   # Start database and core services
   docker compose up -d db adminer dashboard
   ```

4. **Access interfaces**
   - **Dashboard**: http://localhost:8501
   - **Adminer** (DB): http://localhost:8080
     - System: PostgreSQL, Server: db, User: osint, Password: secret, Database: geopolitics

## 📊 Usage

### Collect Data

**Scrape Brookings articles (sitemap-based):**
```bash
docker compose run --rm ingestion scrapy crawl brookings -s LOG_LEVEL=INFO
```

**Collect from French think tanks (RSS):**
```bash
docker compose run --rm ingestion scrapy crawl french_think_tanks_rss -s LOG_LEVEL=INFO
```

### Analyze Content

**Run NLP pipeline:**
```bash
docker compose run --rm nlp python nlp_pipeline.py
```

This will:
- Detect article language (FR/EN)
- Extract named entities (countries, organizations, people)
- Identify geopolitical events: **SANCTIONS**, **TREATIES**, **POSITIONING**

### View Results

1. **Dashboard**: Open http://localhost:8501 for interactive analysis
2. **Database**: Use Adminer at http://localhost:8080 for raw data exploration

## 📈 Data Schema

### Documents Table (Sitemap scraping)
```sql
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  url TEXT UNIQUE NOT NULL,
  title TEXT,
  date_published TIMESTAMPTZ,
  date_collected TIMESTAMPTZ DEFAULT NOW(),
  content_text TEXT,
  content_hash TEXT
);
```

### RSS Feeds Table (RSS scraping)
```sql  
CREATE TABLE rss_feeds (
  id SERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  url TEXT UNIQUE NOT NULL,
  title TEXT,
  description TEXT,
  date_published TIMESTAMPTZ,
  author TEXT,
  categories TEXT[],
  content_text TEXT,
  content_hash TEXT,
  rss_feed_url TEXT
);
```

## 🤖 NLP Pipeline

The system detects three types of geopolitical events:

### Event Types

| Type | Description | Keywords (FR/EN) |
|------|-------------|------------------|
| **SANCTION** | Economic/political sanctions | sanctions, embargo, mesures restrictives |
| **TREATY** | International agreements | accord, traité, treaty, agreement |
| **POSITIONING** | Diplomatic positions | condamne, soutient, condemns, supports |

### Language Support
- **French**: IRIS, IFRI content
- **English**: Brookings, international sources

## 🔧 Development

### Project Structure
```
osint-compose-minimal/
├── ingestion/          # Scrapy spiders & pipelines
│   ├── osint/spiders/
│   │   ├── brookings_spider.py
│   │   └── iris_rss_spider.py  
│   └── requirements.txt
├── nlp/               # NLP analysis pipeline
│   ├── nlp_pipeline.py
│   └── requirements.txt
├── dashboard/         # Streamlit interface  
│   ├── dashboard.py
│   └── requirements.txt
├── db/
│   └── init.sql       # Database schema
└── docker-compose.yml
```

### Adding New Sources

1. Create spider in `ingestion/osint/spiders/`
2. Update pipeline mapping in `ingestion/osint/pipelines.py`
3. Test with: `docker compose run --rm ingestion scrapy crawl your_spider`

### Customizing NLP

Edit `nlp/nlp_pipeline.py`:
- Modify `event_patterns` for new event types
- Add language support in `detect_language()`
- Extend entity extraction rules

## ⚖️ Ethical Guidelines

This project follows responsible OSINT practices:

- ✅ **Respects robots.txt** and ToS
- ✅ **Rate limiting** (1.5s delay between requests)  
- ✅ **Fair use** (research/analysis purposes)
- ✅ **Transparent User-Agent** identification
- ✅ **No paywall circumvention**
- ✅ **Public data only**

## 🗺️ Roadmap

- [x] **S1-S2**: MVP scraping + storage (Brookings + IRIS)
- [x] **S3**: NLP event detection (FR/EN)
- [x] **S4**: Interactive dashboard + visualizations
- [ ] **S5**: Additional sources (CSIS, Atlantic Council, IISS)
- [ ] **S6**: Production deployment (Raspberry Pi + monitoring)
- [ ] **S7**: Advanced NLP (BERT topic modeling, entity linking)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-source`
3. Make changes and test thoroughly
4. Commit with clear messages: `git commit -m "Add CSIS spider"`
5. Push and create Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is designed for **research and educational purposes**. Users are responsible for ensuring compliance with applicable laws and terms of service of target websites.

## 🔗 Useful Links

- **Brookings Institution**: https://www.brookings.edu
- **IRIS France**: https://www.iris-france.org  
- **IFRI**: https://www.ifri.org
- **spaCy Documentation**: https://spacy.io
- **Scrapy Documentation**: https://scrapy.org

---

*Built with ❤️ for the OSINT community*