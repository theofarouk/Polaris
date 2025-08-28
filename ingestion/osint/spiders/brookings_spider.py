import hashlib
import scrapy
import trafilatura

ARTICLE_PATTERNS = (
    "/blog/", "/article/", "/research/", "/topics/", "/essays/",
    "/press-release/", "/report/", "/reports/", "/events/", "/opinion/",
)
MEDIA_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".pdf", ".mp4", ".mp3")

def looks_like_article(url: str) -> bool:
    if any(url.lower().endswith(ext) for ext in MEDIA_EXTS):
        return False
    if "/wp-content/" in url.lower() or "/person-sitemap" in url.lower():
        return False
    return any(p in url.lower() for p in ARTICLE_PATTERNS)

class BrookingsSpider(scrapy.Spider):
    name = "brookings"
    custom_settings = {"DOWNLOAD_DELAY": 1.5, "AUTOTHROTTLE_ENABLED": True}
    allowed_domains = ["brookings.edu"]
    start_urls = ["https://www.brookings.edu/sitemap_index.xml"]

    def parse(self, resp):
        # Suivre tous les sous-sitemaps (xml ou xml.gz)
        for loc in resp.xpath("//*[local-name()='loc']/text()").getall():
            yield scrapy.Request(loc, callback=self.parse_map, dont_filter=True)

    def parse_map(self, resp):
        # Chaque sitemap peut contenir soit d'autres sitemaps, soit des URLs finales
        # Traiter chaque entrée <url> du sitemap
        for url_entry in resp.xpath("//*[local-name()='url']"):
            loc = url_entry.xpath("*[local-name()='loc']/text()").get()
            lastmod = url_entry.xpath("*[local-name()='lastmod']/text()").get()
            
            if not loc:
                continue
                
            url = loc.strip()
            if url.endswith(".xml") or url.endswith(".xml.gz"):
                # encore un sitemap → on descend
                yield scrapy.Request(url, callback=self.parse_map, dont_filter=True)
            else:
                # URL finale : on ne garde que les pages qui ressemblent à des articles
                if looks_like_article(url):
                    # Passer la date lastmod en meta
                    yield scrapy.Request(url, callback=self.parse_article, meta={'lastmod': lastmod})

    def parse_article(self, resp):
        # On s'assure que c'est bien une page HTML
        ctype = resp.headers.get("Content-Type", b"text/html").decode("utf-8").lower()
        if "html" not in ctype:
            return  # ignore images, pdf, etc.

        title = resp.css("h1::text").get() or resp.css("title::text").get()
        
        # Utiliser lastmod du sitemap en priorité, sinon extraire du HTML
        date = resp.meta.get('lastmod')
        if not date:
            date = resp.css("time::attr(datetime)").get() or resp.xpath("//meta[@property='article:published_time']/@content").get()

        text = trafilatura.extract(resp.text, include_comments=False, include_tables=False)
        if not text:
            # fallback simple si Trafilatura n'y arrive pas
            text = " ".join(resp.css("article *::text").getall()).strip() or None

        content_hash = hashlib.sha256((text or "").encode("utf-8")).hexdigest()

        yield {
            "source": "brookings",
            "url": resp.url,
            "title": title,
            "date_published": date,
            "content_text": text,
            "content_hash": content_hash,
        }
