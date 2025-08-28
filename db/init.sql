CREATE TABLE IF NOT EXISTS documents (
  id SERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  url TEXT UNIQUE NOT NULL,
  title TEXT,
  date_published TIMESTAMPTZ,
  date_collected TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  authors TEXT[],
  language TEXT,
  section TEXT,
  content_text TEXT,
  content_hash TEXT,
  tags TEXT[],
  entities JSONB,
  embedding BYTEA
);

CREATE TABLE IF NOT EXISTS rss_feeds (
  id SERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  url TEXT UNIQUE NOT NULL,
  title TEXT,
  description TEXT,
  date_published TIMESTAMPTZ,
  date_collected TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  author TEXT,
  categories TEXT[],
  guid TEXT,
  content_text TEXT,
  content_hash TEXT,
  rss_feed_url TEXT
);
