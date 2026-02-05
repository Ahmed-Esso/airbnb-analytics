from playwright.sync_api import sync_playwright
import json
import re
import time
import csv
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


def get_browser_context(playwright):
    """Create and return a browser context with anti-detection measures"""
    browser = playwright.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
        ]
    )
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        locale="en-US",
        timezone_id="America/New_York",
        extra_http_headers={
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
    )
    return browser, context


def scrape_search_page(search_url: str, max_listings: int = 50) -> List[str]:
    """Scrape Airbnb search page and extract all listing URLs"""
    listing_urls = []
    
    with sync_playwright() as p:
        browser, context = get_browser_context(p)
        try:
            page = context.new_page()
            
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """)
            
            page.goto(search_url, wait_until="domcontentloaded", timeout=90000)
            time.sleep(5)
            
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except:
                pass
            
            time.sleep(3)
            
            for i in range(3):
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                time.sleep(2)
            
            link_selectors = [
                'a[href*="/rooms/"]',
                'div[itemprop="itemListElement"] a',
                'div[data-testid="card-container"] a',
            ]
            
            for selector in link_selectors:
                try:
                    links = page.query_selector_all(selector)
                    for link in links:
                        href = link.get_attribute('href')
                        if href and '/rooms/' in href:
                            if href.startswith('/'):
                                full_url = f"https://www.airbnb.com{href}"
                            else:
                                full_url = href
                            
                            clean_url = full_url.split('?')[0]
                            
                            if clean_url not in listing_urls:
                                listing_urls.append(clean_url)
                                
                        if len(listing_urls) >= max_listings:
                            break
                    
                    if listing_urls:
                        break
                except Exception as e:
                    continue
            
            page.screenshot(path="search_page_screenshot.png")
            
        except Exception as e:
            pass
        finally:
            browser.close()
    
    return listing_urls


def scrape_listing_details(page, url: str) -> Optional[Dict]:
    """Scrape a single listing page for price analysis"""
    data = {
        "realSum": None,
        "room_type": None,
        "room_shared": False,
        "room_private": False,
        "person_capacity": None,
        "host_is_superhost": False,
        "multi": False,
        "biz": False,
        "city": None,
        "lat": None,
        "lng": None,
        "cleanliness_rating": None,
        "guest_satisfaction_overall": None,
        "bedrooms": None,
        "beds": None,
        "bathrooms": None,
        "wifi": False,
        "kitchen": False,
        "air_conditioning": False,
        "parking": False,
        "tv": False,
        "heating": False,
    }
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)
        
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except:
            pass
        
        time.sleep(2)
        
        page_title = page.title().lower()
        h1_elem = page.query_selector('h1')
        h1_text = h1_elem.inner_text().strip().lower() if h1_elem else ""
        
        if "oops" in page_title or "oops" in h1_text or "not found" in page_title:
            return None
        
        listing_id_match = re.search(r'/rooms/(\d+)', url)
        data["id"] = listing_id_match.group(1) if listing_id_match else f"scraped_{hash(url)}"
        
        page_text = ""
        title_text = ""
        try:
            page_text = page.inner_text('body')
            if h1_elem:
                title_text = h1_elem.inner_text().strip().lower()
        except:
            pass
        
        # Extract room type and flags
        try:
            room_types = ["entire home", "entire place", "private room", "shared room", "hotel room"]
            for rt in room_types:
                if rt in title_text or rt in page_text.lower()[:2000]:
                    data["room_type"] = rt.title()
                    if "shared" in rt:
                        data["room_shared"] = True
                    elif "private" in rt:
                        data["room_private"] = True
                    break
            
            if any(word in page_text.lower()[:3000] for word in ["multiple rooms", "several rooms", "多个房间"]):
                data["multi"] = True
            
            if any(word in page_text.lower()[:3000] for word in ["business", "work", "desk", "workspace", "entrepreneur"]):
                data["biz"] = True
        except:
            pass
        
        # Extract city and host info
        try:
            full_title = page.title()
            title_parts = full_title.split(" - ")
            if len(title_parts) >= 2:
                location_part = title_parts[-2] if "Airbnb" in title_parts[-1] else title_parts[-1]
                location_parts = location_part.split(",")
                if location_parts:
                    data["city"] = location_parts[0].strip()
            
            if "superhost" in page_text.lower():
                data["host_is_superhost"] = True
        except:
            pass
        
        # Extract lat/lng from scripts
        try:
            all_scripts_content = ""
            scripts = page.query_selector_all('script')
            for script in scripts:
                try:
                    all_scripts_content += script.inner_text(timeout=1000) + " "
                except:
                    continue
            
            # Try multiple patterns to find coordinates
            lat_patterns = [
                r'"lat"\s*:\s*([-\d.]+)',
                r'"latitude"\s*:\s*([-\d.]+)',
                r'"pdp_listing_detail".*?"lat"\s*:\s*([-\d.]+)',
                r'listing.*?"lat"\s*:\s*([-\d.]+)',
                r'"location".*?"lat"\s*:\s*([-\d.]+)',
            ]
            lng_patterns = [
                r'"lng"\s*:\s*([-\d.]+)',
                r'"longitude"\s*:\s*([-\d.]+)',
                r'"pdp_listing_detail".*?"lng"\s*:\s*([-\d.]+)',
                r'listing.*?"lng"\s*:\s*([-\d.]+)',
                r'"location".*?"lng"\s*:\s*([-\d.]+)',
            ]
            
            for lat_pat, lng_pat in zip(lat_patterns, lng_patterns):
                lat_match = re.search(lat_pat, all_scripts_content)
                lng_match = re.search(lng_pat, all_scripts_content)
                if lat_match and lng_match:
                    lat_val = float(lat_match.group(1))
                    lng_val = float(lng_match.group(1))
                    # Validate coordinates are reasonable (not 0,0)
                    if abs(lat_val) > 0.1 and abs(lng_val) > 0.1:
                        data["lat"] = lat_val
                        data["lng"] = lng_val
                        break
            
            # Fallback: search in page HTML source
            if not data["lat"]:
                try:
                    html_content = page.content()
                    lat_match = re.search(r'"lat"\s*:\s*([-\d.]+)', html_content)
                    lng_match = re.search(r'"lng"\s*:\s*([-\d.]+)', html_content)
                    if lat_match and lng_match:
                        lat_val = float(lat_match.group(1))
                        lng_val = float(lng_match.group(1))
                        if abs(lat_val) > 0.1 and abs(lng_val) > 0.1:
                            data["lat"] = lat_val
                            data["lng"] = lng_val
                except:
                    pass
        except:
            pass
        
        # PERSON_CAPACITY / BEDROOMS / BEDS / BATHROOMS
        try:
            info_text = page_text.lower()
            
            guests_match = re.search(r'(\d+)\s*guest', info_text)
            if guests_match:
                data["person_capacity"] = int(guests_match.group(1))
            
            bedroom_match = re.search(r'(\d+)\s*bedroom', info_text)
            if bedroom_match:
                data["bedrooms"] = int(bedroom_match.group(1))
            
            bed_match = re.search(r'(\d+)\s*bed(?!room)', info_text)
            if bed_match:
                data["beds"] = int(bed_match.group(1))
            
            bath_match = re.search(r'(\d+)\s*bath', info_text)
            if bath_match:
                data["bathrooms"] = int(bath_match.group(1))
        except:
            pass
        
        # REALSUM (PRICE PER NIGHT)

        try:
            price_match = re.search(r'[\$€£¥₹]\s*([\d,]+)\s*(?:per\s*)?(?:/\s*)?night', page_text, re.IGNORECASE)
            if price_match:
                data["realSum"] = int(price_match.group(1).replace(',', ''))
            else:
                price_match2 = re.search(r'[\$€£]([\d,]+)', page_text[:5000])
                if price_match2:
                    data["realSum"] = int(price_match2.group(1).replace(',', ''))
        except:
            pass
        
        # Extract review count
        try:
            review_match = re.search(r'([\d,]+)\s*review', page_text.lower())
            if review_match:
                data["review_count"] = int(review_match.group(1).replace(',', ''))
        except:
            pass
        
        # Extract ratings
        try:
            rating_elem = page.query_selector('span[aria-label*="rating"]')
            if rating_elem:
                rating_text = rating_elem.get_attribute('aria-label') or rating_elem.inner_text()
                rating_match = re.search(r'([\d\.]+)', rating_text)
                if rating_match:
                    val = float(rating_match.group(1))
                    if val <= 5:
                        data["guest_satisfaction_overall"] = val
            
            if not data["guest_satisfaction_overall"]:
                overall_patterns = [
                    r'([\d\.]+)\s*rating',
                    r'rated\s*([\d\.]+)',
                    r'rating[:\s]*([\d\.]+)',
                    r'★\s*([\d\.]+)',
                ]
                for pattern in overall_patterns:
                    rating_match = re.search(pattern, page_text.lower())
                    if rating_match:
                        val = float(rating_match.group(1))
                        if 0 < val <= 5:
                            data["guest_satisfaction_overall"] = val
                            break
            
            cleanliness_match = re.search(r'cleanliness[:\s]*([\d\.]+)', page_text.lower())
            if cleanliness_match:
                val = float(cleanliness_match.group(1))
                if val <= 5:
                    data["cleanliness_rating"] = val
        except:
            pass
        
        # Extract amenities
        try:
            amenities_text = []
            amenities_selectors = [
                '[data-section-id="AMENITIES_DEFAULT"] div[role="listitem"]',
                'div[data-testid="amenity-row"]',
            ]
            
            for selector in amenities_selectors:
                amenity_items = page.query_selector_all(selector)
                if amenity_items:
                    amenities_text = list(set([item.inner_text().strip().lower() for item in amenity_items if item.inner_text().strip()]))
                    if amenities_text:
                        break
            
            if not amenities_text:
                amenities_text = [page_text.lower()]
            
            amenities_str = ' '.join(amenities_text)
            data["wifi"] = any(word in amenities_str for word in ["wifi", "internet", "wi-fi"])
            data["kitchen"] = "kitchen" in amenities_str
            data["air_conditioning"] = any(word in amenities_str for word in ["air conditioning", "ac", "a/c", "cooling"])
            data["parking"] = any(word in amenities_str for word in ["parking", "garage"])
            data["tv"] = any(word in amenities_str for word in ["tv", "television", "hdtv"])
            data["heating"] = "heating" in amenities_str
        except:
            pass
        
        print(f"   [+] Extracted: {data.get('city', 'Unknown')} - {data.get('room_type', 'Unknown')}")
        return data
        
    except Exception as e:
        print(f"   [!] Error: {e}")
        return None


def scrape_all_listings(search_url: str, output_file: str = "airbnb_listings.csv", max_listings: int = 50):
    """
    Main function: scrape search page, then visit each listing for details
    """
    print("=" * 60)
    print("AIRBNB SCRAPER - Multi-Listing Mode")
    print("=" * 60)
    
    # Step 1: Get all listing URLs from search page
    listing_urls = scrape_search_page(search_url, max_listings)
    
    if not listing_urls:
        print("\n[X] No listings found on search page")
        return []
    
    print(f"\n[*] Will scrape {len(listing_urls)} listings...")
    time.sleep(2)
    
    # Step 2: Visit each listing and extract details
    all_data = []
    
    with sync_playwright() as p:
        browser, context = get_browser_context(p)
        try:
            page = context.new_page()
            
            # Add stealth script
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """)
            
            for i, url in enumerate(listing_urls, 1):
                print(f"\n--- Listing {i}/{len(listing_urls)} ---")
                
                data = scrape_listing_details(page, url)
                
                if data:
                    all_data.append(data)
                
                # Delay between requests to avoid rate limiting
                if i < len(listing_urls):
                    delay = 3 + (i % 3)  # 3-5 seconds delay
                    print(f"   [*] Waiting {delay}s before next request...")
                    time.sleep(delay)
                    
        except Exception as e:
            print(f"[!] Error during scraping: {e}")
        finally:
            browser.close()
            print("\n   [*] Browser closed")
    
    # Step 3: Save results
    if all_data:
        # Save as CSV with specific column order
        csv_file = output_file.replace('.json', '.csv') if output_file.endswith('.json') else output_file
        
        # Define column order - all extractable fields
        fieldnames = [
            "realSum",
            "room_type",
            "room_shared",
            "room_private",
            "person_capacity",
            "host_is_superhost",
            "multi",
            "biz",
            "cleanliness_rating",
            "guest_satisfaction_overall",
            "bedrooms",
            "city",
            "lng",
            "lat",
            "beds",
            "bathrooms",
            "wifi",
            "kitchen",
            "air_conditioning",
            "parking",
            "tv",
            "heating",
        ]
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_data)
        
        # Also save as JSON
        json_file = csv_file.replace('.csv', '.json')
        Path(json_file).write_text(json.dumps(all_data, ensure_ascii=False, indent=2), encoding='utf-8')
        
        print("\n" + "=" * 60)
        print(f"[SUCCESS] Scraped {len(all_data)} listings!")
        print(f"   CSV: {csv_file}")
        print(f"   JSON: {json_file}")
        print("=" * 60)
    else:
        print("\n[X] No data extracted")
    
    return all_data


def scrape_airbnb_listing(url: str, output_file: str = "airbnb_detailed.json") -> Optional[Dict]:
    """
    Scrape a single Airbnb listing - simplified version with essential fields only
    """
    data = {
        "room_type": None,
        "city": None,
        "lat": None,
        "lng": None,
        "person_capacity": None,
        "bedrooms": None,
        "beds": None,
        "bathrooms": None,
        "realSum": None,
        "rating_overall": None,
        "rating_cleanliness": None,
        "review_count": None,
        "wifi": False,
        "kitchen": False,
        "air_conditioning": False,
        "parking": False,
        "tv": False,
        "heating": False,
    }

    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                timezone_id="America/New_York",
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                }
            )
            
            page = context.new_page()
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """)

            print(f"[*] Loading: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=90000)
            time.sleep(5)
            
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
                print("   [+] Page fully loaded")
            except:
                print("   [!] Continuing without waiting for networkidle")
            
            time.sleep(3)
            
            # Check for error pages
            page_title = page.title().lower()
            h1_elem = page.query_selector('h1')
            h1_text = h1_elem.inner_text().strip().lower() if h1_elem else ""
            
            if "oops" in page_title or "oops" in h1_text or "not found" in page_title:
                print(f"   [!] ERROR: Invalid listing URL")
                return None
            
            # Get page text
            page_text = page.inner_text('body').lower()
            
            # CITY
            try:
                title_parts = page.title().split(" - ")
                if len(title_parts) >= 2:
                    location_part = title_parts[-2] if "Airbnb" in title_parts[-1] else title_parts[-1]
                    data["city"] = location_part.split(",")[0].strip()
            except:
                pass
            
            # ROOM TYPE
            room_types = ["entire home", "entire place", "private room", "shared room", "hotel room"]
            for rt in room_types:
                if rt in h1_text or rt in page_text[:2000]:
                    data["room_type"] = rt.title()
                    break
            
            # LAT & LNG
            try:
                scripts = page.query_selector_all('script')
                for script in scripts:
                    try:
                        content = script.inner_text(timeout=2000)
                        lat_match = re.search(r'"lat"\s*:\s*([-\d.]+)', content)
                        lng_match = re.search(r'"lng"\s*:\s*([-\d.]+)', content)
                        if lat_match and lng_match:
                            data["lat"] = float(lat_match.group(1))
                            data["lng"] = float(lng_match.group(1))
                            break
                    except:
                        continue
            except:
                pass
            
            # PERSON_CAPACITY / BEDROOMS / BEDS / BATHROOMS
            guests_match = re.search(r'(\d+)\s*guest', page_text)
            if guests_match:
                data["person_capacity"] = int(guests_match.group(1))
            
            bedroom_match = re.search(r'(\d+)\s*bedroom', page_text)
            if bedroom_match:
                data["bedrooms"] = int(bedroom_match.group(1))
            
            bed_match = re.search(r'(\d+)\s*bed(?!room)', page_text)
            if bed_match:
                data["beds"] = int(bed_match.group(1))
            
            bath_match = re.search(r'(\d+)\s*bath', page_text)
            if bath_match:
                data["bathrooms"] = int(bath_match.group(1))
            
            # PRICE (realSum)
            price_match = re.search(r'[\$€£¥₹]\s*([\d,]+)\s*(?:per\s*)?(?:/\s*)?night', page_text, re.IGNORECASE)
            if price_match:
                data["realSum"] = int(price_match.group(1).replace(',', ''))
            else:
                price_match2 = re.search(r'[\$€£]([\d,]+)', page_text[:5000])
                if price_match2:
                    data["realSum"] = int(price_match2.group(1).replace(',', ''))
            
            # RATINGS
            rating_elem = page.query_selector('span[aria-label*="rating"]')
            if rating_elem:
                rating_text = rating_elem.get_attribute('aria-label') or rating_elem.inner_text()
                rating_match = re.search(r'([\d\.]+)', rating_text)
                if rating_match:
                    data["rating_overall"] = float(rating_match.group(1))
            
            cleanliness_match = re.search(r'cleanliness[:\s]*([\d\.]+)', page_text)
            if cleanliness_match:
                val = float(cleanliness_match.group(1))
                if val <= 5:
                    data["rating_cleanliness"] = val
            
            # REVIEW COUNT
            review_match = re.search(r'([\d,]+)\s*review', page_text)
            if review_match:
                data["review_count"] = int(review_match.group(1).replace(',', ''))
            
            # AMENITIES
            amenities_str = page_text
            data["wifi"] = any(word in amenities_str for word in ["wifi", "internet", "wi-fi"])
            data["kitchen"] = "kitchen" in amenities_str
            data["air_conditioning"] = any(word in amenities_str for word in ["air conditioning", "ac", "a/c", "cooling"])
            data["parking"] = any(word in amenities_str for word in ["parking", "garage"])
            data["tv"] = any(word in amenities_str for word in ["tv", "television", "hdtv"])
            data["heating"] = "heating" in amenities_str
            
            print(f"   [+] Extracted: {data.get('city', 'Unknown')} - {data.get('room_type', 'Unknown')}")

        except Exception as main_error:
            print(f"\n[X] Main error during scraping: {main_error}")
            return None
        finally:
            if browser:
                browser.close()
                print("   [*] Browser closed")

    # Save to JSON
    if data.get("city") or data.get("realSum"):
        try:
            Path(output_file).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f"\n[SUCCESS] Data saved to: {output_file}")
            print(f"   City: {data.get('city')}")
            print(f"   Price: {data.get('realSum')}")
            return data
        except Exception as e:
            print(f"[X] Error saving file: {e}")
            return None
    else:
        print("\n[X] Failed to extract main data")
        return None
