import hashlib
import scrapy
import trafilatura
from datetime import datetime
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

class IrisRSSSpider(scrapy.Spider):
    name = "french_think_tanks_rss"
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "AUTOTHROTTLE_ENABLED": True,
        "ITEM_PIPELINES": {
            "osint.pipelines.RSSPipeline": 300,
        },
        "DEFAULT_REQUEST_HEADERS": {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }
    allowed_domains = ["iris-france.org", "ifri.org", "institutdelors.eu"]
    start_urls = [
        "https://www.iris-france.org/feed/",
        "https://www.ifri.org/fr/rss.xml",
        "https://institutdelors.eu/feed/"
    ]

    def parse(self, response):
        # Parser le flux RSS
        try:
            root = ET.fromstring(response.text)
            
            # Trouver tous les items dans le flux RSS
            for item in root.findall('.//item'):
                rss_item = {}
                
                # Extraire les données de base du RSS
                rss_item['title'] = self.get_element_text(item, 'title')
                rss_item['url'] = self.get_element_text(item, 'link')
                rss_item['description'] = self.get_element_text(item, 'description')
                rss_item['date_published'] = self.parse_rss_date(self.get_element_text(item, 'pubDate'))
                rss_item['author'] = self.get_element_text(item, 'dc:creator')
                rss_item['guid'] = self.get_element_text(item, 'guid')
                rss_item['rss_feed_url'] = response.url
                
                # Déterminer la source selon l'URL du flux
                if 'iris-france.org' in response.url:
                    rss_item['source'] = 'iris'
                elif 'ifri.org' in response.url:
                    rss_item['source'] = 'ifri'
                elif 'institutdelors.eu' in response.url:
                    rss_item['source'] = 'institut_delors'
                else:
                    rss_item['source'] = 'unknown'
                
                # Extraire les catégories si disponibles
                categories = []
                for category in item.findall('category'):
                    if category.text:
                        categories.append(category.text.strip())
                rss_item['categories'] = categories
                
                # Extraire le contenu complet si disponible dans content:encoded
                content_encoded = self.get_element_text(item, 'content:encoded')
                if content_encoded:
                    # Utiliser Trafilatura pour nettoyer le HTML du content:encoded
                    text = trafilatura.extract(content_encoded, include_comments=False, include_tables=True)
                    if text:
                        rss_item['content_text'] = text
                        rss_item['content_hash'] = hashlib.sha256(text.encode("utf-8")).hexdigest()
                        yield rss_item
                        continue
                
                # Si pas de content:encoded ou si l'extraction échoue, aller chercher le contenu sur la page
                if rss_item['url']:
                    yield scrapy.Request(
                        url=rss_item['url'],
                        callback=self.parse_full_article,
                        meta={'rss_item': rss_item}
                    )
                else:
                    # Sinon, utiliser juste la description du RSS
                    rss_item['content_text'] = self.clean_html_description(rss_item.get('description', ''))
                    rss_item['content_hash'] = hashlib.sha256((rss_item['content_text'] or "").encode("utf-8")).hexdigest()
                    yield rss_item
                    
        except ET.ParseError as e:
            self.logger.error(f"Erreur de parsing XML pour {response.url}: {e}")

    def parse_full_article(self, response):
        rss_item = response.meta['rss_item']
        
        # Extraire le contenu complet avec Trafilatura
        text = trafilatura.extract(response.text, include_comments=False, include_tables=True)
        if not text:
            # Fallback sur la description RSS si l'extraction échoue
            text = self.clean_html_description(rss_item.get('description', ''))
        
        rss_item['content_text'] = text
        rss_item['content_hash'] = hashlib.sha256((text or "").encode("utf-8")).hexdigest()
        
        yield rss_item

    def get_element_text(self, element, tag):
        """Récupère le texte d'un élément XML en gérant les namespaces"""
        # Gestion des namespaces communs
        namespaces = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'content': 'http://purl.org/rss/1.0/modules/content/'
        }
        
        # Essayer d'abord sans namespace
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        
        # Essayer avec namespace si le tag contient ':'
        if ':' in tag:
            prefix, local_tag = tag.split(':', 1)
            if prefix in namespaces:
                ns_tag = f"{{{namespaces[prefix]}}}{local_tag}"
                child = element.find(ns_tag)
                if child is not None and child.text:
                    return child.text.strip()
        
        return None

    def clean_html_description(self, description):
        """Nettoie la description HTML du RSS"""
        if not description:
            return ""
        
        # Utiliser Trafilatura pour nettoyer le HTML de la description
        cleaned = trafilatura.extract(description, include_comments=False, include_tables=False)
        return cleaned if cleaned else description

    def parse_rss_date(self, date_str):
        """Parse les dates RSS (format RFC 2822)"""
        if not date_str:
            return None
        
        try:
            # Format RSS standard: "Thu, 14 Aug 2025 15:44:31 +0000"
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Impossible de parser la date: {date_str} - {e}")
            return None