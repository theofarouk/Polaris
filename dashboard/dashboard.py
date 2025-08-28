import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import psycopg2
from datetime import datetime
from collections import Counter

# Configuration de la page
st.set_page_config(
    page_title="OSINT Geopolitical Dashboard",
    page_icon="🌍",
    layout="wide"
)

@st.cache_data
def load_nlp_results():
    """Charge les résultats NLP depuis le fichier JSON"""
    try:
        with open('/app/nlp/nlp_results.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Fichier nlp_results.json non trouvé. Lance d'abord le pipeline NLP.")
        return []

@st.cache_data
def load_articles_from_db():
    """Charge les articles depuis la base de données"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "geopolitics"),
            user=os.getenv("DB_USER", "osint"),
            password=os.getenv("DB_PASSWORD", "secret"),
        )
        
        query = """
        SELECT id, title, url, date_published, date_collected, source
        FROM rss_feeds 
        WHERE source = 'iris'
        ORDER BY date_published DESC
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"Erreur de connexion à la base : {e}")
        return pd.DataFrame()

def create_event_summary(nlp_results):
    """Crée un résumé des événements détectés"""
    all_events = []
    for doc in nlp_results:
        for event in doc['events']:
            all_events.append({
                'doc_id': doc['doc_id'],
                'event_type': event['event_type'],
                'keyword': event['keyword'],
                'context': event['context'],
                'targets': event['targets'],
                'organizations': event['organizations']
            })
    
    return pd.DataFrame(all_events)

def create_entity_summary(nlp_results):
    """Crée un résumé des entités détectées"""
    all_entities = []
    for doc in nlp_results:
        for entity in doc['entities']:
            all_entities.append({
                'doc_id': doc['doc_id'],
                'text': entity['text'],
                'label': entity['label']
            })
    
    return pd.DataFrame(all_entities)

# Interface principale
def main():
    st.title("🌍 OSINT Geopolitical Dashboard")
    st.markdown("**Analyse des tendances géopolitiques** - Think Tank IRIS")
    
    # Chargement des données
    nlp_results = load_nlp_results()
    articles_df = load_articles_from_db()
    
    if not nlp_results:
        st.warning("Aucun résultat NLP trouvé.")
        return
    
    # Métriques principales
    st.header("📊 Vue d'ensemble")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Articles analysés", len(nlp_results))
    
    with col2:
        total_events = sum(len(doc['events']) for doc in nlp_results)
        st.metric("Événements détectés", total_events)
    
    with col3:
        total_entities = sum(len(doc['entities']) for doc in nlp_results)
        st.metric("Entités extraites", total_entities)
    
    with col4:
        languages = [doc['language'] for doc in nlp_results]
        main_lang = Counter(languages).most_common(1)[0][0]
        st.metric("Langue principale", main_lang.upper())
    
    # Analyse des événements
    st.header("🚨 Analyse des événements géopolitiques")
    
    events_df = create_event_summary(nlp_results)
    
    if not events_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Répartition des types d'événements
            event_counts = events_df['event_type'].value_counts()
            
            fig_pie = px.pie(
                values=event_counts.values,
                names=event_counts.index,
                title="Répartition des types d'événements",
                color_discrete_map={
                    'SANCTION': '#ff6b6b',
                    'TREATY': '#4ecdc4', 
                    'POSITIONING': '#45b7d1'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Top mots-clés par événement
            keyword_counts = events_df['keyword'].value_counts().head(10)
            
            fig_bar = px.bar(
                x=keyword_counts.values,
                y=keyword_counts.index,
                orientation='h',
                title="Mots-clés les plus fréquents",
                labels={'x': 'Occurrences', 'y': 'Mot-clé'}
            )
            fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Analyse des entités
    st.header("🏛️ Entités nommées")
    
    entities_df = create_entity_summary(nlp_results)
    
    if not entities_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Répartition par type d'entité
            entity_type_counts = entities_df['label'].value_counts()
            
            fig_entities = px.bar(
                x=entity_type_counts.index,
                y=entity_type_counts.values,
                title="Répartition des types d'entités",
                labels={'x': 'Type d\'entité', 'y': 'Nombre'}
            )
            st.plotly_chart(fig_entities, use_container_width=True)
        
        with col2:
            # Top entités mentionnées
            entity_counts = entities_df['text'].value_counts().head(15)
            
            fig_top_entities = px.bar(
                x=entity_counts.values,
                y=entity_counts.index,
                orientation='h',
                title="Entités les plus mentionnées",
                labels={'x': 'Mentions', 'y': 'Entité'}
            )
            fig_top_entities.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_top_entities, use_container_width=True)
    
    # Détails des articles
    st.header("📰 Détails des articles")
    
    # Merge avec les données d'articles pour avoir les titres
    article_details = []
    for doc in nlp_results:
        # Trouver le titre correspondant
        article_row = articles_df[articles_df['id'] == doc['doc_id']]
        title = article_row['title'].iloc[0] if not article_row.empty else f"Article {doc['doc_id']}"
        url = article_row['url'].iloc[0] if not article_row.empty else "#"
        
        article_details.append({
            'ID': doc['doc_id'],
            'Titre': title,
            'URL': url,
            'Langue': doc['language'],
            'Nb Entités': len(doc['entities']),
            'Nb Événements': len(doc['events']),
            'Types événements': ', '.join(set([e['event_type'] for e in doc['events']]))
        })
    
    details_df = pd.DataFrame(article_details)
    st.dataframe(details_df, use_container_width=True)
    
    # Section de détail par article
    st.header("🔍 Exploration détaillée")
    
    selected_article = st.selectbox(
        "Sélectionne un article pour voir le détail :",
        options=[(doc['doc_id'], f"Article {doc['doc_id']}") for doc in nlp_results],
        format_func=lambda x: f"{x[1]} ({len([e for doc in nlp_results if doc['doc_id'] == x[0] for e in doc['events']])} événements)"
    )
    
    if selected_article:
        doc_id = selected_article[0]
        selected_doc = next((doc for doc in nlp_results if doc['doc_id'] == doc_id), None)
        
        if selected_doc:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🚨 Événements détectés")
                for event in selected_doc['events']:
                    with st.expander(f"{event['event_type']}: {event['keyword']}"):
                        st.write(f"**Contexte:** {event['context']}")
                        if event['targets']:
                            st.write(f"**Cibles:** {', '.join(event['targets'])}")
                        if event['organizations']:
                            st.write(f"**Organisations:** {', '.join(event['organizations'])}")
            
            with col2:
                st.subheader("🏛️ Entités extraites")
                entities_by_type = {}
                for entity in selected_doc['entities']:
                    label = entity['label']
                    if label not in entities_by_type:
                        entities_by_type[label] = []
                    entities_by_type[label].append(entity['text'])
                
                for label, entities in entities_by_type.items():
                    st.write(f"**{label}:** {', '.join(set(entities))}")

if __name__ == "__main__":
    main()