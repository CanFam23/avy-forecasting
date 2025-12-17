from playwright.sync_api import sync_playwright
from datetime import datetime
import pandas as pd
import re
import os

BASE_URLS = ['https://www.flatheadavalanche.org/avalanche-forecast/#/whitefish-range',
             'https://www.flatheadavalanche.org/avalanche-forecast/#/swan-range',
             'https://www.flatheadavalanche.org/avalanche-forecast/#/flathead-range-&-glacier-np']

ARCHIVE_URL = 'https://www.flatheadavalanche.org/avalanche-forecast/#/archive/forecast'

def scrape_current_forecast():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        forecast_data = []
        for url in BASE_URLS:
            page.goto(url)
            
            forecast_data.append(scrape_page(page))
        browser.close()
        
    for data in forecast_data:
        if data['date'].date() != datetime.now().date():
            print(data['date'])
            print("Most recent forecast not valid for today!")
        
    return pd.DataFrame(forecast_data).drop_duplicates()

def scrape_page(page):
    danger_box = page.locator('div.nac-dangerToday').first
    forecast_data = {}
            
    zone = page.locator("h2.nac-gray-700.nac-m-0.nac-h2").first.inner_text().lower().strip()
    
    forecast_data['zone_name'] = zone
    
    date = danger_box.locator(".nac-dangerDate").first.inner_html()
    
    forecast_data['date'] = datetime.strptime(date, "%A, %B %d, %Y")
    
    bands = danger_box.locator(".nac-elevationBlock")
    
    for i in range(bands.count()):
        elevation_band = bands.nth(i).locator(".nac-elevationLabel").inner_text().split("Elevation")[0].lower().strip()
                        
        danger_rating = bands.nth(i).locator(".nac-dangerLabel").inner_text().split(" - ")[0]
        
        forecast_data[elevation_band if elevation_band not in ["mid-","low"] else "middle" if elevation_band == "mid-" else "lower"] = int(danger_rating)
    return forecast_data

def scrape_archives(day: datetime) -> pd.DataFrame:
    forecast_data = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(ARCHIVE_URL)
        
        page.wait_for_selector("div.nac-card.nac-card-hover.nac-archive-card", timeout=10000)
        
        cards = page.locator("div.nac-card.nac-card-hover.nac-archive-card")
        
        for i in range(cards.count()):
            text = cards.nth(i).text_content()
            date_split = text.split(" ")[:3] # type: ignore
            date_split[2] = re.sub(r"\D", "", date_split[2])
            date = datetime.strptime(" ".join(date_split), "%b %d, %Y")

            
            if date == day:
                print(text)
                cards.nth(i).click()
                print(f"New URL: {page.url}")
                page.wait_for_load_state('networkidle')
                
                forecast_data.append(scrape_page(page))
                
                page.go_back()
                page.wait_for_load_state('networkidle')
                
                # IMPORTANT: Re-get the cards locator
                cards = page.locator("div.nac-card")
        browser.close()
    return pd.DataFrame(forecast_data).drop_duplicates()

if __name__ == "__main__":
    # day = datetime(2025, 12, i)
    data = scrape_current_forecast()
    
    if os.path.exists("data/2526_FAC/FAC_danger_levels_25.csv") and os.path.getsize("data/2526_FAC/FAC_danger_levels_25.csv") > 0:
        data.to_csv("data/2526_FAC/FAC_danger_levels_25.csv", index=False, header=False, mode='a')
    else:
        data.to_csv("data/2526_FAC/FAC_danger_levels_25.csv", index=False, header=True, mode='w')

