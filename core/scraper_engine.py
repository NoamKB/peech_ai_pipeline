from playwright.sync_api import sync_playwright
from core.classifier import classify_headline
from core.database import save_to_db

def scrape_site(page, site):
    name = site["name"]
    url = site["url"]
    selector = site.get("selector")
    page.goto(url, timeout=60000, wait_until="domcontentloaded")

    selectors = [selector] if selector else ["h1", "h2", "a"]
    headlines = []

    for sel in selectors:
        try:
            headlines.extend(page.locator(sel).all_text_contents())
        except:
            continue

    for headline in list(h.strip() for h in headlines if h.strip())[:10]:
        category, raw_label, confidence = classify_headline(headline)
        save_to_db(name, headline, category, raw_label, confidence)
        print(f"[{name}] {headline} --> [{category}] (raw: {raw_label}, conf: {confidence:.2f})")

def scrape_all_sites(websites):
    if not websites:
        return
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for site in websites:
            try:
                scrape_site(page, site)
            except Exception as e:
                print(f"Failed to scrape {site['name']}: {e}")
        browser.close()

