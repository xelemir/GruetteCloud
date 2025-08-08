import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

data = [
    {
        "name": "Edeka Simonis",
        "url": "https://www.edeka.de/eh/s%C3%BCdwest/e-center-simonis-stammheimer-stra%C3%9Fe-10/angebote.jsp",
        "location": "Stammheimer Straße 10, 70435 Stuttgart",
        "items": [
            "oatly",
            "frosta fertiggerichte",
            "garden gourmet sensational burger",
            "planted chicken kräuter & zitrone",
        ]
    },
    {
        "name": "Edeka Sehrer",
        "url": "https://www.edeka.de/eh/s%C3%BCdwest/edeka-sehrer-eisenbahnstra%C3%9Fe-58/angebote.jsp",
        "location": "Eisenbahnstraße 58, 70188 Stuttgart",
        "items": [
            "oatly",
            "frosta fertiggerichte",
            "garden gourmet sensational burger",
            "planted chicken kräuter & zitrone",
        ]
    }
]


def fetch_edeka_data():
    """
    Scrapes EDEKA offers using headless Chrome for server deployment.
    """
    # Chrome options for headless server deployment
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.images": 2
    })
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        all_offers = []
        
        for store in data:
            print(f"Fetching data for {store['name']}...")
            
            try:
                driver.get(store['url'])
                time.sleep(8)  # Wait for page to load
                
                # Find offer containers using the more reliable container class
                offer_containers = driver.find_elements(By.CSS_SELECTOR, 'div.css-1olgk07')
                print(f"Found {len(offer_containers)} offer containers")
                
                offers = []
                target_items = [item.lower() for item in store['items']]
                
                for container in offer_containers:
                    try:
                        # Look for the title span within each container
                        # Product titles can have various CSS classes like css-163h5df, css-i72elb, etc.
                        title_spans = container.find_elements(By.CSS_SELECTOR, 'span[class^="css-"]')
                        
                        for span in title_spans:
                            offer_text = span.text.strip()
                            # Filter for actual product titles (skip prices, descriptions, etc.)
                            if offer_text and len(offer_text) > 5 and not offer_text.replace('.', '').replace(',', '').replace(' ', '').isdigit():
                                offers.append(offer_text)
                                
                                # Check if this offer matches target items
                                for target in target_items:
                                    if target in offer_text.lower():
                                        print(f"✅ Found target item: {offer_text}")
                                break  # Only take the first meaningful title from each container
                                
                    except Exception as e:
                        # Skip containers that cause issues
                        continue
                
                print(f"Found {len(offers)} offers from {store['name']}")
                all_offers.extend(offers)
                
            except Exception as e:
                print(f"Error processing {store['name']}: {e}")
        
        return all_offers
        
    except Exception as e:
        print(f"Error setting up browser: {e}")
        return []
        
    finally:
        if 'driver' in locals():
            driver.quit()


if __name__ == "__main__":
    offers = fetch_edeka_data()
    print(f"\nTotal offers found: {len(offers)}")