import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import time

def scrape_trustpilot(business_url, max_reviews=30):
    all_reviews = []
    page = 1
    
    # Standard headers to look like a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    while len(all_reviews) < max_reviews:
        print(f"Scraping page {page}...")
        url = f"{business_url}?page={page}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

        soup = BeautifulSoup(response.content, "html.parser")
        
        # Trustpilot stores data in a script tag with id "__NEXT_DATA__"
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if not script_tag:
            print("Could not find the data script tag. The page structure might have changed.")
            break
            
        data = json.loads(script_tag.string)
        
        # Navigate through the JSON structure to find reviews
        # Path: props -> pageProps -> reviews
        reviews_list = data.get("props", {}).get("pageProps", {}).get("reviews", [])
        
        if not reviews_list:
            break

        for r in reviews_list:
            if len(all_reviews) >= max_reviews:
                break
                
            review_data = {
                "user_name": r.get("consumer", {}).get("displayName"),
                "rating": r.get("rating"),
                "title": r.get("title"),
                "content": r.get("text"),
                "date": r.get("dates", {}).get("publishedDate"),
                "verified": r.get("isVerified")
            }
            all_reviews.append(review_data)

        # Respectful delay between pages
        page += 1
        time.sleep(2)

    # Save to CSV
    df = pd.DataFrame(all_reviews)
    df.to_csv("reviews.csv", index=False, encoding="utf-8")
    print(f"Successfully saved {len(df)} reviews to reviews.csv")

# --- EXECUTION ---
# Replace with the URL of the business you want to scrape
TARGET_URL = "https://www.trustpilot.com/review/www.apple.com" 
scrape_trustpilot(TARGET_URL, max_reviews=30)