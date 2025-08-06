# News Scraping and Classification Pipeline

A simple end-to-end pipeline that scrapes news headlines, classifies them using AI, and stores the results in a database.

## Features

- **Web Scraping**: Uses Playwright to scrape headlines from news websites
- **AI Classification**: Uses HuggingFace transformers to classify headlines into categories
- **Database Storage**: SQLite database for storing scraped data
- **Configurable**: JSON configuration file for website settings

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install playwright transformers torch
playwright install
```

## Usage

1. Create a `config.json` file with your websites:
```json
{
  "websites": [
    {
      "name": "BBC News",
      "url": "https://www.bbc.com/news",
      "selector": "h2"
    }
  ]
}
```

2. Run the scraper:
```bash
python scraper.py
```

## How it works

1. **Scraping**: Uses Playwright to load websites and extract headlines using CSS selectors
2. **Classification**: Uses the CardiffNLP tweet-topic model to classify headlines into categories
3. **Storage**: Saves results to SQLite database with source, headline, category, and timestamp

## Categories

- World News
- Sports  
- Entertainment
- Politics
- Technology
- Business
- Health
- General News

## Database Schema

```sql
CREATE TABLE headlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    headline TEXT,
    category TEXT,
    scraped_at TIMESTAMP
)
```




