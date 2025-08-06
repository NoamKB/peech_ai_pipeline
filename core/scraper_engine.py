"""
This module provides the ScraperEngine class for extracting headlines from websites,
classifying them using a zero-shot AI model, and saving results to the database.
"""
from playwright.sync_api import sync_playwright

class ScraperEngine:
    def __init__(self, classifier, db):
        """
        Initializes the ScraperEngine with a classifier and database instance.
        """
        self.classifier = classifier
        self.db = db

    def extract_headlines(self, page, site):
        """
        Extracts headlines from a given site using Playwright.
        Returns a list of headline strings.
        """
        name = site["name"]
        url = site["url"]
        selector = site.get("selector")
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_selector(selector or "#video-title", timeout=10000)

        selectors = [selector] if selector else ["h1", "h2", "a"]
        headlines = []
        for sel in selectors:
            try:
                headlines.extend(page.locator(sel).all_text_contents())
            except Exception:
                continue
        print("Extracted headlines:", headlines)
        return [h.strip() for h in headlines if h.strip()][:10]

    def classify_headlines(self, headlines, candidate_labels, confidence_threshold=0.3):
        results = []
        for headline in headlines:
            category, scores, raw_result = self.classifier.classify(headline, candidate_labels)
            best_score = max(scores)
            
            # Only include if confidence is above threshold
            if best_score >= confidence_threshold:
                results.append((headline, category, scores, raw_result))
            else:
                print(f"Skipping '{headline}' - confidence too low: {best_score:.2f}")
        return results

    def save_headlines(self, source, classified_headlines):
        """
        Saves classified headlines to the database using batch processing.
        """
        if not classified_headlines:
            return
            
        # Prepare batch data
        batch_data = []
        for headline, category, scores, raw_result in classified_headlines:
            best_score = max(scores)
            batch_data.append((source, headline, category, str(scores), best_score))
        
        # Save entire batch at once
        self.db.save_batch(batch_data)

    def process_site(self, page, site, candidate_labels):
        """
        Orchestrates the extraction, classification, and saving for a single site.
        """
        headlines = self.extract_headlines(page, site)
        classified = self.classify_headlines(headlines, candidate_labels)
        self.save_headlines(site["name"], classified)
        for headline, category, scores, raw_result in classified:
            best_score = max(scores)
            print(f"[{site['name']}] {headline} --> [{category}] (conf: {best_score:.2f})")

    def scrape_all_sites(self, websites, candidate_labels):
        """
        Main entry point: scrapes all sites in the list, classifies, and saves results.
        """
        if not websites:
            return
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            for site in websites:
                try:
                    self.process_site(page, site, candidate_labels)
                except Exception as e:
                    print(f"Failed to process {site['name']}: {e}")
            browser.close()
