import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime

class TrustpilotScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_business_reviews(self, business_url, num_reviews=30):
        """
        Scrape reviews from Trustpilot business page
        """
        print(f"🔍 Scraping reviews from: {business_url}")
        
        reviews_data = []
        
        try:
            # Extract business name from URL
            business_name_match = re.search(r'/review/([\w-]+)', business_url)
            business_name = business_name_match.group(1) if business_name_match else "Unknown"
            
            # Construct review page URL
            base_url = business_url.rstrip('/')
            
            # Scrape multiple pages
            page = 1
            while len(reviews_data) < num_reviews:
                page_url = f"{base_url}?page={page}"
                print(f"📄 Scraping page {page}...")
                
                response = requests.get(page_url, headers=self.headers)
                
                if response.status_code != 200:
                    print(f"❌ Failed to fetch page {page}")
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find review cards - Trustpilot structure
                review_cards = soup.find_all('article', {'class': 'review'})
                
                if not review_cards:
                    print(f"⚠️ No reviews found on page {page}")
                    break
                
                for review in review_cards:
                    if len(reviews_data) >= num_reviews:
                        break
                    
                    # Extract review data
                    review_data = self.extract_review_data(review, business_name)
                    if review_data:
                        reviews_data.append(review_data)
                
                page += 1
                time.sleep(1)  # Be respectful to the server
                
            print(f"✅ Scraped {len(reviews_data)} reviews")
            
            # Create DataFrame
            df = pd.DataFrame(reviews_data)
            df.to_csv('reviews.csv', index=False)
            print(f"💾 Saved to reviews.csv")
            
            return df
            
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return None
    
    def extract_review_data(self, review_element, business_name):
        """
        Extract individual review data from HTML element
        """
        try:
            # Rating
            rating_element = review_element.find('div', {'class': 'star-rating'})
            rating = None
            if rating_element:
                rating_match = re.search(r'(\d+)', str(rating_element))
                if rating_match:
                    rating = int(rating_match.group(1))
            
            # Title
            title_element = review_element.find('h2', {'class': 'review-title'})
            title = title_element.text.strip() if title_element else "No title"
            
            # Content
            content_element = review_element.find('p', {'class': 'review-content'})
            content = content_element.text.strip() if content_element else "No content"
            
            # Date
            date_element = review_element.find('time')
            date = date_element.get('datetime', datetime.now().strftime('%Y-%m-%d')) if date_element else datetime.now().strftime('%Y-%m-%d')
            
            # Reviewer name
            reviewer_element = review_element.find('span', {'class': 'consumer-information__name'})
            reviewer_name = reviewer_element.text.strip() if reviewer_element else "Anonymous"
            
            return {
                'business_name': business_name,
                'reviewer_name': reviewer_name,
                'rating': rating,
                'title': title,
                'content': content,
                'date': date,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"Error extracting review: {e}")
            return None

# Test function
if __name__ == "__main__":
    scraper = TrustpilotScraper()
    # Test with a sample URL
    test_url = "https://www.trustpilot.com/review/apple.com"
    df = scraper.scrape_business_reviews(test_url, num_reviews=10)
    
    if df is not None:
        print("\n📊 Sample scraped data:")
        print(df[['title', 'rating', 'date']].head())