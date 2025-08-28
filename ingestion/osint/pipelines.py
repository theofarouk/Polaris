import os
import psycopg2

class PostgresPipeline:
    def open_spider(self, spider):
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "geopolitics"),
            user=os.getenv("DB_USER", "osint"),
            password=os.getenv("DB_PASSWORD", "secret"),
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()

    def process_item(self, item, spider):
        self.cur.execute(
            '''
            INSERT INTO documents (source, url, title, date_published, content_text, content_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
              title = EXCLUDED.title,
              date_published = EXCLUDED.date_published,
              content_text = EXCLUDED.content_text,
              content_hash = EXCLUDED.content_hash;
            ''',
            (
                item.get("source"),
                item.get("url"),
                item.get("title"),
                item.get("date_published"),
                item.get("content_text"),
                item.get("content_hash"),
            ),
        )
        return item


class RSSPipeline:
    def open_spider(self, spider):
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "geopolitics"),
            user=os.getenv("DB_USER", "osint"),
            password=os.getenv("DB_PASSWORD", "secret"),
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()

    def process_item(self, item, spider):
        self.cur.execute(
            '''
            INSERT INTO rss_feeds (source, url, title, description, date_published, author, categories, guid, content_text, content_hash, rss_feed_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
              title = EXCLUDED.title,
              description = EXCLUDED.description,
              date_published = EXCLUDED.date_published,
              author = EXCLUDED.author,
              categories = EXCLUDED.categories,
              content_text = EXCLUDED.content_text,
              content_hash = EXCLUDED.content_hash;
            ''',
            (
                item.get("source"),
                item.get("url"),
                item.get("title"),
                item.get("description"),
                item.get("date_published"),
                item.get("author"),
                item.get("categories"),
                item.get("guid"),
                item.get("content_text"),
                item.get("content_hash"),
                item.get("rss_feed_url"),
            ),
        )
        return item
