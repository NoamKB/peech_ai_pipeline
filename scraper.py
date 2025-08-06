import json
import sqlite3
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
from transformers import pipeline
import os

# Load a news-trained classifier instead of a tweet-trained one
model_name = "cardiffnlp/tweet-topic-21-multi"
classifier = pipeline("text-classification", model=model_name, tokenizer=model_name)

db_path = "news.db"

# Check if we need to recreate the DB
db_exists = os.path.exists(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

if not db_exists:
    cursor.execute("""
    CREATE TABLE headlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        headline TEXT,
        category TEXT,
        raw_label TEXT,
        confidence REAL,
        scraped_at TIMESTAMP
    )
    """)
    conn.commit()
else:
    # Check if the schema needs to be updated
    try:
        cursor.execute("SELECT raw_label FROM headlines LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("DROP TABLE IF EXISTS headlines")
        cursor.execute("""
        CREATE TABLE headlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            headline TEXT,
            category TEXT,
            raw_label TEXT,
            confidence REAL,
            scraped_at TIMESTAMP
        )
        """)
        conn.commit()

def classify_headline(headline):
    tragedy_keywords = ["died", "death", "killed", "injured", "attack", "murder"]

    result = classifier(headline, top_k=3)
    best = max(result, key=lambda x: x["score"])
    label = best["label"]
    score = best["score"]

    mapping = {
        "news_&_social_concern": "World News",
        "sports": "Sports",
        "music": "Entertainment",
        "arts_&_culture": "Entertainment",
        "celebrity_&_pop_culture": "Entertainment",
        "politics": "Politics",
        "science_&_technology": "Technology",
        "business_&_entrepreneurs": "Business",
        "health": "Health",
        "family": "General News",
        "education": "General News",
        "diaries_&_daily_life": "General News",
        "film_tv_&_video": "Entertainment",
        "environmental_issues": "World News",
        "other": "General News"
    }

    category = mapping.get(label, "General News")

    # Apply tragedy rule only if confidence is low
    if score < 0.5 and any(word in headline.lower() for word in tragedy_keywords):
        category = "World News"

    return category, label, score

def save_to_db(source, headline, category, raw_label, confidence):
    cursor.execute(
        "INSERT INTO headlines (source, headline, category, raw_label, confidence, scraped_at) VALUES (?, ?, ?, ?, ?, ?)",
        (source, headline, category, raw_label, confidence, datetime.now())
    )
    conn.commit()

def scrape_site(page, name, url, selector=None):
    page.goto(url, timeout=60000, wait_until="domcontentloaded")

    selectors = [selector] if selector else ["h1", "h2", "a"]
    headlines = []

    for sel in selectors:
        try:
            elements = page.locator(sel).all_text_contents()
            headlines.extend(elements)
        except:
            pass

    unique_headlines = list({h.strip() for h in headlines if h.strip()})

    for title in unique_headlines[:10]:
        category, raw_label, confidence = classify_headline(title)
        save_to_db(name, title, category, raw_label, confidence)
        print(f"[{name}] {title} --> [{category}] (raw: {raw_label}, conf: {confidence:.2f})")

def main():
    config_path = Path("config.json")

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        websites = config.get("websites", [])
    else:
        websites = []

    if not websites:
        url = input("Enter the website URL: ").strip()
        name = input("Enter a name for this source: ").strip()
        selector = input("Enter CSS selector (or press Enter for auto): ").strip() or None
        websites = [{"name": name, "url": url, "selector": selector}]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site in websites:
            print(f"\nScraping {site['name']} ({site['url']})...")
            try:
                scrape_site(page, site['name'], site['url'], site.get('selector'))
            except Exception as e:
                print(f"Failed to scrape {site['name']}: {e}")

        browser.close()

if __name__ == "__main__":
    main()
    conn.close()
