import spacy
import re
import os
import psycopg2
from langdetect import detect
from datetime import datetime
import json

class GeopoliticalNLP:
    def __init__(self):
        # On va utiliser les modèles de base pour commencer
        # Si tu veux installer les gros modèles plus tard: python -m spacy download en_core_web_trf
        try:
            self.nlp_en = spacy.load("en_core_web_sm")
        except OSError:
            print("Modèle spaCy anglais non trouvé. Installe avec: python -m spacy download en_core_web_sm")
            self.nlp_en = None
            
        try:
            self.nlp_fr = spacy.load("fr_core_news_sm") 
        except OSError:
            print("Modèle spaCy français non trouvé. Installe avec: python -m spacy download fr_core_news_sm")
            self.nlp_fr = None
            
        # Patterns de détection d'événements (inspiré de ta roadmap)
        self.event_patterns = {
            "SANCTION": {
                "fr": r"\b(sanction(s)?|embargo|gel des avoirs|mesures? restrictives?|boycott|interdiction)\b",
                "en": r"\b(sanction(s)?|embargo|asset freeze|listing|restrictive measures?|boycott|ban)\b"
            },
            "TREATY": {
                "fr": r"\b(accord|traité|MoU|ratification|signature|convention|protocole)\b", 
                "en": r"\b(accord|treat(y|ies)|agreement|MoU|ratification|signature|convention|protocol)\b"
            },
            "POSITIONING": {
                "fr": r"\b(condamne|soutient|s'oppose|dénonce|critique|approuve|rejette|position|stance)\b",
                "en": r"\b(condemn(s)?|support(s)?|oppose(s)?|denounce(s)?|criticize(s)?|approve(s)?|reject(s)?|position|stance|urge(s)?|call(s) on)\b"
            }
        }
        
    def detect_language(self, text):
        """Détecte la langue du texte"""
        try:
            return detect(text[:1000])  # Utilise les 1000 premiers chars pour la détection
        except:
            return "en"  # Défaut anglais
            
    def extract_entities(self, text, language="en"):
        """Extrait les entités nommées (pays, orgs, personnes)"""
        nlp = self.nlp_en if language == "en" else self.nlp_fr
        if not nlp:
            return []
            
        doc = nlp(text)
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in ("GPE", "ORG", "PERSON", "NORP"):  # Geo, Org, Person, Nationalities
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
                
        return entities
        
    def detect_events(self, text, language="en"):
        """Détecte les événements géopolitiques dans le texte"""
        events = []
        text_lower = text.lower()
        
        # Extraire les entités pour context
        entities = self.extract_entities(text, language)
        countries = [e["text"] for e in entities if e["label"] in ("GPE", "NORP")]
        orgs = [e["text"] for e in entities if e["label"] == "ORG"]
        
        # Détecter chaque type d'événement
        for event_type, patterns in self.event_patterns.items():
            pattern = patterns.get(language, patterns["en"])
            
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Contexte autour du match (50 chars avant/après)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                events.append({
                    "event_type": event_type,
                    "keyword": match.group(),
                    "context": context,
                    "targets": countries[:3],  # Max 3 pays pour éviter le bruit
                    "organizations": orgs[:3],
                    "confidence": 0.6,  # Score de base
                    "position": match.start()
                })
                
        return events
        
    def process_document(self, doc_id, title, content):
        """Traite un document complet"""
        language = self.detect_language(content)
        
        # Traiter titre + contenu
        full_text = f"{title or ''} {content or ''}"
        
        entities = self.extract_entities(full_text, language)
        events = self.detect_events(full_text, language)
        
        return {
            "doc_id": doc_id,
            "language": language,
            "entities": entities,
            "events": events,
            "processed_at": datetime.now().isoformat()
        }

def process_iris_articles():
    """Traite tous les articles IRIS en base"""
    nlp_processor = GeopoliticalNLP()
    
    # Connexion DB
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "geopolitics"), 
        user=os.getenv("DB_USER", "osint"),
        password=os.getenv("DB_PASSWORD", "secret"),
    )
    
    cur = conn.cursor()
    
    # Récupérer tous les articles IRIS
    cur.execute("""
        SELECT id, title, content_text 
        FROM rss_feeds 
        WHERE source = 'iris' 
        AND content_text IS NOT NULL
    """)
    
    articles = cur.fetchall()
    print(f"Traitement de {len(articles)} articles IRIS...")
    
    results = []
    for article_id, title, content in articles:
        print(f"Traitement article {article_id}: {title[:50]}...")
        
        result = nlp_processor.process_document(article_id, title, content)
        results.append(result)
        
        # Afficher résumé
        print(f"  - Langue: {result['language']}")
        print(f"  - Entités: {len(result['entities'])}")
        print(f"  - Événements: {len(result['events'])}")
        
        # Afficher événements détectés
        for event in result['events']:
            print(f"    * {event['event_type']}: '{event['keyword']}' (targets: {event['targets']})")
    
    # Sauvegarder en JSON pour le dashboard
    with open('nlp_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\nRésultats sauvegardés dans nlp_results.json")
    
    cur.close()
    conn.close()
    
    return results

if __name__ == "__main__":
    results = process_iris_articles()