from core.scraper_engine import scrape_all_sites
from core.database import init_db, close_db
from pathlib import Path
import json

def main():
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        websites = config.get("websites", [])
    else:
        websites = []

    init_db()
    scrape_all_sites(websites)
    close_db()

if __name__ == "__main__":
    main()
