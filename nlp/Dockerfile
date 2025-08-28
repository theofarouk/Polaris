FROM python:3.11-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier requirements NLP
COPY requirements.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Télécharger les modèles spaCy (français et anglais)
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download fr_core_news_sm

# Copier le code NLP
COPY . /app

CMD ["bash"]