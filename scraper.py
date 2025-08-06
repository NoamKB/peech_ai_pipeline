"""
Main entry point for the news scraping and classification pipeline.

This script loads configuration, initializes the database, and runs the scraping pipeline.
Refactored for modularity: scraping, classification, and storage are handled by separate components, now encapsulated in ScraperEngine.
"""
from core.scraper_engine import ScraperEngine
from core.classifier import HeadlineClassifier
from core.database import Database
from pathlib import Path
import json

def main():
    config_path = Path("config.json")
    config = {}
    
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error reading config file: {e}")
            return
        except Exception as e:
            print(f"Unexpected error reading config: {e}")
            return
    
    websites = config.get("websites", [])
    categories = config.get("categories", [])
    
    if not websites:
        print("No websites configured. Please check your config.json file.")
        return
    
    if not categories:
        print("No categories configured. Please check your config.json file.")
        return

    db_path = config.get("db_path", "youtube.db")
    
    try:
        # Initialize database with connection pooling (3 connections)
        db = Database(db_path, pool_size=3)
        db.init_db()
        #db.clear_all_data()  # Clear old data
        
        classifier = HeadlineClassifier()
        engine = ScraperEngine(classifier, db)
        engine.scrape_all_sites(websites, categories)
        
        # Print database statistics
        stats = db.get_stats()
        print(f"\n=== Database Statistics ===")
        print(f"Total records: {stats['total_records']}")
        print(f"Total sources: {stats['total_sources']}")
        print(f"Pending batch size: {stats['pending_batch_size']}")
        
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main()
