import requests
from bs4 import BeautifulSoup
import os
import time
import re

BASE_URL = "https://kdp.aks.ac.kr/inde"
LIST_URL = f"{BASE_URL}/search?itemId=14&pageUnit=202"
SAVE_DIR = "/Users/a12/projects/tts/aks_classics"

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename).replace(" ", "_")

def scrape():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

# Targeted IDs from the user (ID codes)
    id_codes = [
        "2_29321", "1_21914", "2_35526", "1_21927", "1_21763", "1_8508",
        "2_29678", "1_125", "2_10940", "2_32857", "2_29562", "2_32306",
        "2_33113", "1_21771", "1_21892", "2_15789", "2_37158", "2_17785",
        "2_30696", "2_37182"
    ]
    
    # Prepend the required prefix to form full IDs
    item_ids = [f"POKS.GUBI.GUBI.{code}" for code in id_codes]
    
    # Required headers and cookies identified through browser research
    headers = {
        "Referer": "https://kdp.aks.ac.kr/inde/search?itemId=14",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    }
    cookies = {
        "POKS_ES_SSESSIONID": "64B3367E89519CB8621AAC27CDE36DB5"
    }

    print(f"Starting targeted download for {len(item_ids)} items with custom headers.")

    for i, item_id in enumerate(item_ids):
        # The URL also needs the itemId=14 parameter
        detail_url = f"{BASE_URL}/indeData?itemId=14&id={item_id}"
        print(f"[{i+1}/{len(item_ids)}] Scraping: {detail_url}")
        
        try:
            res = requests.get(detail_url, headers=headers, cookies=cookies)
            if res.status_code != 200:
                print(f"  Failed: {res.status_code}")
                continue
            
            detail_soup = BeautifulSoup(res.text, 'html.parser')
            
            # Anchor-based Extraction (More robust against class changes)
            title = f"item_{item_id}"
            th_title = detail_soup.find('th', string=re.compile("제목"))
            if th_title:
                td_title = th_title.find_next_sibling('td')
                if td_title:
                    title = td_title.get_text(strip=True)
            
            # Extract transcript (채록내용) - Anchor-based
            transcript_content = ""
            th_target = detail_soup.find('th', string=re.compile("채록내용"))
            if th_target:
                td_target = th_target.find_next_sibling('td')
                if td_target:
                    transcript_content = td_target.get_text(separator="\n", strip=True)
            
            if not transcript_content:
                # Last resort: dump everything between certain markers or just the whole text
                transcript_content = detail_soup.get_text(separator="\n", strip=True)

            filename = f"{i+1:03d}_{sanitize_filename(title)}.txt"
            filepath = os.path.join(SAVE_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"ID: {item_id}\n")
                f.write(f"URL: {detail_url}\n")
                f.write(f"TITLE: {title}\n")
                f.write("-" * 50 + "\n\n")
                f.write(transcript_content)
            
            print(f"  Saved: {filename}")
            time.sleep(0.5) # Gentle delay
            
        except Exception as e:
            print(f"  Error scraping {item_id}: {e}")

if __name__ == "__main__":
    scrape()
