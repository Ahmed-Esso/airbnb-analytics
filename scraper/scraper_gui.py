import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import threading
import json
import csv
import re
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# Check if playwright is installed
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class AirbnbScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Airbnb Scraper")
        self.root.geometry("800x700")
        self.root.configure(bg="white")
        
        # Variables
        self.is_running = False
        self.scraped_data = []
        self.parallel_workers = 3
        self.weekend_mode = False
        self.city_buttons = {}  # Store city buttons for color management
        self.selected_city = None
        self.executor = None  # Store executor reference for immediate cancellation
        
        self.setup_ui()
        
    def setup_ui(self):
        # Configure custom styles
        style = ttk.Style()
        style.configure("City.TButton", background="white")
        style.map("City.TButton", 
                  background=[('active', '#FFE8EC'), ('!active', 'white')])
        style.configure("SelectedCity.TButton", background="#FF385C", foreground="white")
        style.map("SelectedCity.TButton",
                  background=[('active', '#E31C5F'), ('!active', '#FF385C')],
                  foreground=[('active', 'white'), ('!active', 'white')])
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo (embedded as base64)
        try:
            from PIL import Image, ImageTk
            import base64
            from io import BytesIO
            
            # Airbnb logo embedded as base64
            logo_path = Path(__file__).parent / 'logo_base64.txt'
            logo_base64 = open(logo_path, 'r').read()
            logo_data = base64.b64decode(logo_base64)
            logo_image = Image.open(BytesIO(logo_data))
            logo_image = logo_image.resize((300, 100), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = tk.Label(main_frame, image=logo_photo, bg="white")
            logo_label.image = logo_photo  # Keep a reference!
            logo_label.pack(pady=10)
        except Exception as e:
            # Fallback to text if image fails to load
            title_label = ttk.Label(main_frame, text=" Airbnb Scraper", font=("Helvetica", 20, "bold"))
            title_label.pack(pady=10)
        
        # Mode selection frame
        mode_frame = ttk.LabelFrame(main_frame, text="Scraping Mode", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.mode_var = tk.StringVar(value="city")
        ttk.Radiobutton(mode_frame, text="Search by City", variable=self.mode_var, value="city", command=self.on_mode_change).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Custom Search URL", variable=self.mode_var, value="url", command=self.on_mode_change).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Single Listing", variable=self.mode_var, value="single", command=self.on_mode_change).pack(side=tk.LEFT, padx=10)
        
        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        # City/URL input
        self.input_label = ttk.Label(input_frame, text="City Name:")
        self.input_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.input_entry = ttk.Entry(input_frame, width=60)
        self.input_entry.grid(row=0, column=1, padx=10, pady=5)
        self.input_entry.insert(0, "Paris")
        
        # Max listings
        ttk.Label(input_frame, text="Max Listings:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.max_listings_var = tk.StringVar(value="20")
        self.max_listings_entry = ttk.Entry(input_frame, width=10, textvariable=self.max_listings_var)
        self.max_listings_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Parallel workers
        ttk.Label(input_frame, text="Parallel Workers:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.workers_var = tk.StringVar(value="3")
        self.workers_entry = ttk.Entry(input_frame, width=10, textvariable=self.workers_var)
        self.workers_entry.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Popular cities buttons
        cities_frame = ttk.Frame(input_frame)
        cities_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Label(cities_frame, text="Quick Select:").pack(side=tk.LEFT, padx=5)
        
        btn_all = ttk.Button(cities_frame, text="All Cities", width=11, 
                           command=self.scrape_all_cities, style="Accent.TButton")
        btn_all.pack(side=tk.LEFT, padx=2)
        
        self.cities_list = ["Amsterdam", "Athens", "Barcelona", "Berlin", "Budapest", 
                  "Lisbon", "London", "Paris", "Rome", "Vienna"]
        for city in self.cities_list:
            btn = ttk.Button(cities_frame, text=city, width=9, 
                           command=lambda c=city: self.set_city(c), style="City.TButton")
            btn.pack(side=tk.LEFT, padx=2)
            self.city_buttons[city] = btn
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="Start Scraping", command=self.start_scraping, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = ttk.Button(btn_frame, text="Export CSV", command=self.export_csv, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(btn_frame, text="Clear Log", command=self.clear_log)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Helvetica", 10))
        self.status_label.pack(pady=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = ScrolledText(log_frame, height=15, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results Summary", padding="5")
        results_frame.pack(fill=tk.X, pady=5)
        
        self.results_var = tk.StringVar(value="No data scraped yet")
        ttk.Label(results_frame, textvariable=self.results_var, font=("Helvetica", 10)).pack()
        
        if not PLAYWRIGHT_AVAILABLE:
            self.log("WARNING: Playwright not installed. Run: pip install playwright")
            self.log("Then run: playwright install chromium")
            self.start_btn.config(state=tk.DISABLED)
    
    def on_mode_change(self):
        mode = self.mode_var.get()
        if mode == "city":
            self.input_label.config(text="City Name:")
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, "Paris")
            self.max_listings_entry.config(state=tk.NORMAL)
        elif mode == "url":
            self.input_label.config(text="Search URL:")
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, "https://www.airbnb.com/s/Paris/homes")
            self.max_listings_entry.config(state=tk.NORMAL)
        else:
            self.input_label.config(text="Listing URL:")
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, "https://www.airbnb.com/rooms/12345678")
            self.max_listings_entry.config(state=tk.DISABLED)
    
    def set_city(self, city):
        self.mode_var.set("city")
        self.on_mode_change()
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, city)
        
        # Reset previous selection
        if self.selected_city and self.selected_city in self.city_buttons:
            self.city_buttons[self.selected_city].config(style="City.TButton")
        
        # Highlight new selection
        if city in self.city_buttons:
            self.city_buttons[city].config(style="SelectedCity.TButton")
            self.selected_city = city
    
    def scrape_all_cities(self):
        """Scrape all cities sequentially"""
        if self.is_running:
            messagebox.showwarning("Already Running", "Scraper is already running!")
            return
        
        if not PLAYWRIGHT_AVAILABLE:
            messagebox.showerror("Error", "Playwright is not installed!\n\nInstall with: pip install playwright\nThen run: playwright install chromium")
            return
        
        # Confirm action
        result = messagebox.askyesno(
            "Scrape All Cities", 
            f"This will scrape all {len(self.cities_list)} cities:\n" + 
            ", ".join(self.cities_list) + "\n\n" +
            f"Max {self.max_listings_var.get()} listings per city.\n\n" +
            "This may take a long time. Continue?"
        )
        
        if not result:
            return
        
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.DISABLED)
        
        # Run in thread
        thread = threading.Thread(target=self._scrape_all_cities_worker, daemon=True)
        thread.start()
    
    def _scrape_all_cities_worker(self):
        """Worker to scrape all cities"""
        total_cities = len(self.cities_list)
        
        for idx, city in enumerate(self.cities_list, 1):
            if not self.is_running:
                self.log("\n Stopped by user")
                break
            
            self.log(f"\n{'='*60}")
            self.log(f" [{idx}/{total_cities}] Starting {city}...")
            self.log(f"{'='*60}\n")
            
            # Set city and scrape
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, city)
            
            # Save current count to detect new listings
            before_count = len(self.scraped_data)
            
            # Call the regular scraping logic
            self._run_scraping(city_mode=True)
            
            # Auto-save after each city if new data was added
            after_count = len(self.scraped_data)
            if after_count > before_count:
                # Save only the new listings for this city
                new_listings = self.scraped_data[before_count:after_count]
                self.auto_save_city(city, new_listings)
            
            # Brief pause between cities
            if idx < total_cities and self.is_running:
                self.log(f"\n⏳ Waiting 5 seconds before next city...\n")
                time.sleep(5)
        
        self.log(f"\n{'='*60}")
        self.log(f"ALL CITIES COMPLETED!")
        self.log(f"Total scraped: {len(self.scraped_data)} listings across all cities")
        self.log(f"{'='*60}")
        
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        if self.scraped_data:
            self.export_btn.config(state=tk.NORMAL)
    
    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.scraped_data = []
        self.results_var.set("No data scraped yet")
        self.export_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
    
    def start_scraping(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.scraped_data = []
        
        # Run in thread to avoid freezing UI
        thread = threading.Thread(target=self.scrape_thread)
        thread.daemon = True
        thread.start()
    
    def stop_scraping(self):
        self.is_running = False
        self.status_var.set("Stopping...")
        self.log("Stopping scraper immediately...")
        
        # Cancel all pending futures immediately
        if self.executor:
            try:
                self.executor.shutdown(wait=False, cancel_futures=True)
                self.log("Cancelled all pending tasks")
            except:
                pass
    
    def scrape_thread(self):
        try:
            self._run_scraping(city_mode=False)
        except Exception as e:
            self.log(f"Error: {str(e)}")
        finally:
            self.is_running = False
            self.root.after(0, self.scraping_complete)
    
    def _run_scraping(self, city_mode=False):
        """Core scraping logic - can be called for single or all cities"""
        try:
            mode = self.mode_var.get()
            input_value = self.input_entry.get().strip()
            max_listings = int(self.max_listings_var.get())
            
            if mode == "city":
                city = input_value.replace(" ", "-")
                search_url = f"https://www.airbnb.com/s/{city}/homes?currency=USD"
                
                if not city_mode:
                    self.log(f"Searching for listings in: {input_value}")
                self.scrape_search(search_url, max_listings, city)
            elif mode == "url":
                url_input = input_value
                if 'currency=' not in url_input:
                    separator = '&' if '?' in url_input else '?'
                    url_input = f"{url_input}{separator}currency=USD"
                self.log(f"Scraping search URL...")
                self.scrape_search(url_input, max_listings, "custom")
            else:
                single_url = input_value
                if 'currency=' not in single_url:
                    separator = '&' if '?' in single_url else '?'
                    single_url = f"{single_url}{separator}currency=USD"
                self.log(f"Scraping single listing...")
                self.scrape_single(single_url)
                
        except Exception as e:
            self.log(f"Error: {e}")
    
    def scrape_search(self, search_url, max_listings, name):
        with sync_playwright() as p:
            browser = None
            try:
                self.status_var.set("Launching browser...")
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
                )
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    locale="en-US",
                    timezone_id="Europe/London",
                    extra_http_headers={
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                page = context.new_page()
                
                # Advanced stealth
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    window.chrome = {runtime: {}};
                """)
                
                self.status_var.set("Loading search page...")
                self.log(f"Loading: {search_url}")
                page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(3)
                
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except:
                    pass
                
                # Progressive URL extraction with scrolling
                self.log(f"Extracting listings (target: {max_listings})...")
                
                listing_urls = []
                consecutive_no_change = 0
                scroll_count = 0
                max_scrolls = 150  # Safety limit
                
                while len(listing_urls) < max_listings and scroll_count < max_scrolls and consecutive_no_change < 8:
                    if not self.is_running:
                        break
                    
                    previous_count = len(listing_urls)
                    
                    # Scroll to bottom of page
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1.2)  # Longer wait for content to load
                    scroll_count += 1
                    
                    # Extract URLs after each scroll
                    selectors = [
                        'a[href*="/rooms/"]',
                        'div[data-testid="card-container"] a',
                    ]
                    
                    for selector in selectors:
                        try:
                            links = page.query_selector_all(selector)
                            for link in links:
                                href = link.get_attribute('href')
                                if href and '/rooms/' in href:
                                    if href.startswith('/'):
                                        href = f"https://www.airbnb.com{href}"
                                    clean_url = href.split('?')[0]
                                    if clean_url not in listing_urls:
                                        listing_urls.append(clean_url)
                                if len(listing_urls) >= max_listings:
                                    break
                            if len(listing_urls) >= max_listings:
                                break
                        except:
                            continue
                    
                    # Check if we found new listings
                    if len(listing_urls) == previous_count:
                        consecutive_no_change += 1
                    else:
                        consecutive_no_change = 0
                    
                    # Log progress every 5 scrolls
                    if scroll_count % 5 == 0:
                        self.log(f"   Found {len(listing_urls)} listings (scrolled {scroll_count}x, no change: {consecutive_no_change})...")
                
                self.log(f"Scrolling complete - found {len(listing_urls)} listings")
                
                page.screenshot(path="search_debug.png")
                
                if not listing_urls:
                    self.log("No listings found")
                    return
                
                self.log("Extracting prices from search results...")
                price_data = {}
                try:
                    # More efficient: use selector to find price elements directly
                    price_elements = page.query_selector_all('[data-testid="price-availability-row"] span, span._tyxjp1, span[class*="price"]')
                    
                    prices = []
                    for elem in price_elements[:len(listing_urls) * 2]:  # Get a bit more in case of duplicates
                        try:
                            text = elem.inner_text()
                            # Extract first number found
                            match = re.search(r'\$(\d+)', text)
                            if match:
                                price_val = int(match.group(1))
                                if 5 < price_val < 50000:  # Reasonable price range
                                    prices.append(price_val)
                        except:
                            continue
                    
                    for i, url in enumerate(listing_urls):
                        if i < len(prices):
                            price_data[url] = prices[i]
                        
                except Exception as e:
                    self.log(f"Price extraction from search failed: {str(e)[:50]}")
                
                # Extract city from search URL
                import re
                city_match = re.search(r'/s/([^/]+)/homes', search_url)
                city_name = None
                if city_match:
                    city_name = city_match.group(1).replace('-', ' ').replace('%20', ' ').title()
                    self.log(f"City: {city_name}")
                
                # Close the search browser
                if browser:
                    browser.close()
                
                # Get number of parallel workers from input
                try:
                    max_workers = int(self.workers_var.get())
                    max_workers = max(1, min(max_workers, 10))  # Limit between 1-10
                except:
                    max_workers = 3
                
                self.log(f"Starting parallel scraping ({max_workers} threads)...")
                
                self.executor = ThreadPoolExecutor(max_workers=max_workers)
                try:
                    # Submit all scraping tasks with price data
                    future_to_url = {
                        self.executor.submit(self.scrape_single_listing, url, i+1, len(listing_urls), city_name, price_data.get(url)): url 
                        for i, url in enumerate(listing_urls)
                    }
                    
                    # Process completed tasks
                    completed = 0
                    for future in as_completed(future_to_url):
                        if not self.is_running:
                            self.executor.shutdown(wait=False, cancel_futures=True)
                            break
                        
                        url = future_to_url[future]
                        completed += 1
                        progress = (completed / len(listing_urls)) * 100
                        self.progress_var.set(progress)
                        self.status_var.set(f"Completed {completed}/{len(listing_urls)}...")
                finally:
                    # Clean up executor
                    if self.executor:
                        self.executor.shutdown(wait=False)
                        self.executor = None
                        
                        try:
                            data = future.result()
                            if data:
                                self.scraped_data.append(data)
                                self.log(f"[{completed}/{len(listing_urls)}] {data.get('city', '?')} - {data.get('room_type', '?')}")
                            else:
                                self.log(f"[{completed}/{len(listing_urls)}] Failed")
                        except Exception as e:
                            self.log(f"[{completed}/{len(listing_urls)}] Error: {str(e)[:50]}")
                
            finally:
                pass  # Browser already closed above
    
    def scrape_single_listing(self, url: str, index: int, total: int, city_name: str = None, search_price: int = None) -> Optional[Dict]:
        """Scrape a single listing in a separate browser instance (for parallel processing)"""
        with sync_playwright() as p:
            browser = None
            try:
                browser = p.chromium.launch(
                    headless=True, 
                    args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
                )
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    locale="en-US"
                )
                page = context.new_page()
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                """)
                
                # Force USD currency in listing URL
                if 'currency=' not in url:
                    separator = '&' if '?' in url else '?'
                    url = f"{url}{separator}currency=USD"
                
                # Extract data
                data = self.extract_listing(page, url)
                
                # Override city with correct value from search URL
                if data and city_name:
                    data['city'] = city_name
                
                if data and search_price and not data.get('realSum'):
                    data['realSum'] = search_price
                    self.log(f"Using search price: ${search_price}")
                
                return data
                
            except Exception as e:
                return None
            finally:
                if browser:
                    browser.close()
    
    def scrape_single(self, url):
        """Single listing mode (from button)"""
        with sync_playwright() as p:
            browser = None
            try:
                self.status_var.set("Launching browser...")
                browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                self.progress_var.set(50)
                data = self.extract_listing(page, url)
                if data:
                    self.scraped_data.append(data)
                    self.log(f"Scraped: {data.get('city', 'Unknown')}")
                self.progress_var.set(100)
                
            finally:
                if browser:
                    browser.close()
    
    def extract_json_from_page(self, page_html: str) -> List[Dict]:
        """Extract JSON data from script tags in the page"""
        json_pool = []
        
        # Extract __NEXT_DATA__ (most reliable for Airbnb)
        next_data_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', page_html, re.DOTALL)
        if next_data_match:
            try:
                data = json.loads(next_data_match.group(1).strip())
                json_pool.append(data)
            except:
                pass
        
        # Extract application/ld+json
        for match in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', page_html, re.DOTALL):
            try:
                data = json.loads(match.group(1).strip())
                if isinstance(data, dict):
                    json_pool.append(data)
                elif isinstance(data, list):
                    json_pool.extend([x for x in data if isinstance(x, dict)])
            except:
                pass
        
        # Extract application/json
        for match in re.finditer(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', page_html, re.DOTALL):
            raw = match.group(1).strip()
            if raw.startswith("{") and raw.endswith("}"):
                try:
                    json_pool.append(json.loads(raw))
                except:
                    pass
        
        return json_pool
    
    def deep_find_in_json(self, obj, keys: List[str]):
        """Recursively search for keys in nested JSON"""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower().replace("_", "").replace("-", "") in [key.lower().replace("_", "").replace("-", "") for key in keys]:
                    return v
            for v in obj.values():
                result = self.deep_find_in_json(v, keys)
                if result is not None:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = self.deep_find_in_json(item, keys)
                if result is not None:
                    return result
        return None
    
    def extract_room_type_from_json(self, json_pool: List[Dict]) -> Optional[str]:
        """Extract room type from JSON data (most reliable method)"""
        # Search for room type in JSON
        for obj in json_pool:
            room_type = self.deep_find_in_json(obj, [
                "roomType", "room_type", "roomTypeCategory", 
                "roomTypeName", "room_type_category", "room_type_name",
                "propertyType", "property_type"
            ])
            
            if room_type and isinstance(room_type, str):
                rt = room_type.lower()
                # Normalize to standard types
                if "entire" in rt and ("home" in rt or "apartment" in rt or "place" in rt):
                    return "Entire home/apt"
                elif "private room" in rt or "room in" in rt:
                    return "Private room"
                elif "shared room" in rt:
                    return "Shared room"
                elif "hotel" in rt:
                    return "Hotel room"
                else:
                    return room_type
        
        # Fallback: search in text fields
        for obj in json_pool:
            for text_key in ["name", "title", "description"]:
                text = self.deep_find_in_json(obj, [text_key])
                if text and isinstance(text, str):
                    t = text.lower()
                    if "entire place" in t or "entire home" in t or "entire apartment" in t:
                        return "Entire home/apt"
                    elif "private room" in t:
                        return "Private room"
                    elif "shared room" in t:
                        return "Shared room"
                    elif "hotel room" in t:
                        return "Hotel room"
        
        return None
    
    def extract_listing(self, page, url) -> Optional[Dict]:
        """Extract data from a single listing page - complete version"""
        data = {
            # URL
            "url": url,
            
            # Price & Room Info
            "realSum": None,
            "room_type": None,
            "room_shared": False,
            "room_private": False,
            "person_capacity": None,
            "host_is_superhost": False,
            "multi": False,
            "biz": False,
            
            # Location
            "city": None,
            "lat": None,
            "lng": None,
            
            # Ratings
            "cleanliness_rating": None,
            "guest_satisfaction_overall": None,
            
            # Property Details
            "bedrooms": None,
            "beds": None,
            "bathrooms": None,
            
            # Amenities
            "wifi": False,
            "kitchen": False,
            "air_conditioning": False,
            "parking": False,
            "tv": False,
            "heating": False,
        }
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except:
                pass
            
            # Check for error page
            page_title = page.title().lower()
            if "oops" in page_title or "not found" in page_title:
                return None
            
            # Get full page text
            page_text = ""
            try:
                page_text = page.inner_text('body').lower()
            except:
                pass
            
            # ═══════════════════════════════════════════════
            # CITY & HOST INFO
            # ═══════════════════════════════════════════════
            full_title = page.title()
            
            # Method 1: Extract city from URL
            import re
            city_from_url = re.search(r'/s/([^/]+)/homes', url) or re.search(r'/rooms/.*[?&].*city=([^&]+)', url)
            if city_from_url:
                data["city"] = city_from_url.group(1).replace('-', ' ').replace('%20', ' ').title()
            
            # Method 2: From page title (last part before Airbnb)
            if not data["city"]:
                parts = full_title.split(" - ")
                for part in reversed(parts):
                    if "airbnb" not in part.lower() and len(part) > 2:
                        # Get city name (first word that looks like a city)
                        city_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', part)
                        if city_match:
                            data["city"] = city_match.group(1)
                            break
            
            # Check if host is superhost
            if "superhost" in page_text:
                data["host_is_superhost"] = True
            
            # ═══════════════════════════════════════════════
            # ROOM TYPE & FLAGS
            # ═══════════════════════════════════════════════
            h1 = page.query_selector('h1')
            title_text = h1.inner_text().strip().lower() if h1 else ""
            
            # Get full HTML for better extraction
            html_content = page.content().lower()
            
            # ═══════════════════════════════════════════════
            # PROPERTY DETAILS (beds, bedrooms) - JSON extraction first
            # ═══════════════════════════════════════════════
            
            # Get HTML content for JSON extraction
            html_content = page.content()
            json_pool = self.extract_json_from_page(html_content)
            
            # Extract beds from JSON first
            if json_pool:
                beds_json = self.deep_find_in_json(json_pool, [
                    "beds", "bedCount", "bed_count", "numberOfBeds", "bedsCount"
                ])
                if beds_json:
                    try:
                        data["beds"] = int(beds_json)
                    except:
                        pass
            
            # Fallback: Extract beds from text
            if not data["beds"]:
                details_patterns = [
                    r'(\d+)\s*(?:single|double|queen|king|twin|full)\s*beds?',
                    r'(\d+)\s*beds?\s*·',
                    r'(\d+)\s*beds?\s*•',
                ]
                for pattern in details_patterns:
                    bed_match = re.search(pattern, page_text)
                    if bed_match:
                        data["beds"] = int(bed_match.group(1))
                        break
            
            # Extract bedrooms from JSON first
            if json_pool:
                bedrooms_json = self.deep_find_in_json(json_pool, [
                    "bedrooms", "bedroomCount", "bedroom_count", "numberOfBedrooms", "bedroomsCount"
                ])
                if bedrooms_json:
                    try:
                        data["bedrooms"] = int(bedrooms_json)
                    except:
                        pass
            
            # Fallback: Extract bedrooms from text
            if not data["bedrooms"]:
                bedroom_patterns = [
                    r'(\d+)\s*bedrooms?\s*·',
                    r'(\d+)\s*bedrooms?\s*•',
                    r'(\d+)\s*bedrooms?[^a-z]',
                ]
                for pattern in bedroom_patterns:
                    bedroom_match = re.search(pattern, page_text)
                    if bedroom_match:
                        data["bedrooms"] = int(bedroom_match.group(1))
                        break
            
            # ═══════════════════════════════════════════════
            # ROOM TYPE - JSON extraction first (MOST RELIABLE)
            # ═══════════════════════════════════════════════
            try:
                
                # Reuse json_pool from above (already extracted for beds/bedrooms)
                if json_pool:
                    data["room_type"] = self.extract_room_type_from_json(json_pool)
                    if data["room_type"]:
                        # Set flags based on room type
                        if "private room" in data["room_type"].lower():
                            data["room_private"] = True
                        elif "shared room" in data["room_type"].lower():
                            data["room_shared"] = True
                
                # Method 2: Check all h2 elements (fallback)
                if not data["room_type"]:
                    h2_elements = page.query_selector_all('h2')
                    for h2 in h2_elements:
                        try:
                            h2_text = h2.inner_text().strip().lower()
                            if "room in" in h2_text:
                                data["room_type"] = "Private room"
                                data["room_private"] = True
                                break
                            elif "entire" in h2_text and ("home" in h2_text or "apartment" in h2_text):
                                data["room_type"] = "Entire home/apt"
                                break
                            elif "shared room" in h2_text:
                                data["room_type"] = "Shared room"
                                data["room_shared"] = True
                                break
                            elif "hotel room" in h2_text:
                                data["room_type"] = "Hotel room"
                                break
                        except:
                            continue
                
                # Method 3: Check HTML if h2 didn't work
                if not data["room_type"]:
                    html_lower = html_content.lower()
                    html_start = html_lower[:1000]
                    if "room in" in html_start and "shared bathroom" in page_text:
                        data["room_type"] = "Private room"
                        data["room_private"] = True
                    elif "private room in" in html_start or "room in" in html_start:
                        data["room_type"] = "Private room"
                        data["room_private"] = True
                    elif "entire home" in html_start or "entire apartment" in html_start or "entire place" in html_start:
                        data["room_type"] = "Entire home/apt"
                    elif "shared room in" in html_start:
                        data["room_type"] = "Shared room"
                        data["room_shared"] = True
                    elif "hotel room" in html_start:
                        data["room_type"] = "Hotel room"
                
                # Method 4: Fallback to page text search
                if not data["room_type"]:
                    page_start = page_text[:2000].lower()
                    if "entire home" in page_start or "entire apartment" in page_start:
                        data["room_type"] = "Entire home/apt"
                    elif "private room" in page_start:
                        data["room_type"] = "Private room"
                        data["room_private"] = True
                    elif "shared room" in page_start:
                        data["room_type"] = "Shared room"
                        data["room_shared"] = True
                    elif "hotel room" in page_start:
                        data["room_type"] = "Hotel room"
            except Exception as e:
                pass
            
            # ═══════════════════════════════════════════════
            # LAT & LNG - Multiple extraction methods
            # ═══════════════════════════════════════════════
            try:
                # Get all script content
                all_scripts = ""
                scripts = page.query_selector_all('script')
                for script in scripts:
                    try:
                        all_scripts += script.inner_text(timeout=1000) + " "
                    except:
                        continue
                
                # Try multiple patterns
                lat_patterns = [
                    r'"lat"\s*:\s*([-\d.]+)',
                    r'"latitude"\s*:\s*([-\d.]+)',
                    r'listing.*?"lat"\s*:\s*([-\d.]+)',
                ]
                lng_patterns = [
                    r'"lng"\s*:\s*([-\d.]+)',
                    r'"longitude"\s*:\s*([-\d.]+)',
                    r'listing.*?"lng"\s*:\s*([-\d.]+)',
                ]
                
                for lat_pat, lng_pat in zip(lat_patterns, lng_patterns):
                    lat_m = re.search(lat_pat, all_scripts)
                    lng_m = re.search(lng_pat, all_scripts)
                    if lat_m and lng_m:
                        lat_val = float(lat_m.group(1))
                        lng_val = float(lng_m.group(1))
                        if abs(lat_val) > 0.1 and abs(lng_val) > 0.1:
                            data["lat"] = lat_val
                            data["lng"] = lng_val
                            break
                
                # Fallback: search in page HTML
                if not data["lat"]:
                    html_content = page.content()
                    lat_m = re.search(r'"lat"\s*:\s*([-\d.]+)', html_content)
                    lng_m = re.search(r'"lng"\s*:\s*([-\d.]+)', html_content)
                    if lat_m and lng_m:
                        lat_val = float(lat_m.group(1))
                        lng_val = float(lng_m.group(1))
                        if abs(lat_val) > 0.1 and abs(lng_val) > 0.1:
                            data["lat"] = lat_val
                            data["lng"] = lng_val
            except:
                pass
            
            # ═══════════════════════════════════════════════
            # REALSUM (PRICE PER NIGHT)
            # ═══════════════════════════════════════════════
            # REALSUM (PRICE PER NIGHT) - Improved with wait_for_selector
            # ═══════════════════════════════════════════════
            # Method 1: Wait for price element to load
            try:
                price_selectors = [
                    'span._1y74zjx',
                    'span._tyxjp1',
                    'div._1jo4hgw span',
                    'span[class*="price"]',
                ]
                for selector in price_selectors:
                    try:
                        price_elem = page.wait_for_selector(selector, timeout=3000)
                        if price_elem:
                            price_text = price_elem.inner_text()
                            # Extract numbers (works for $123 or 123$)
                            price_num = re.search(r'([\d,]+)', price_text)
                            if price_num:
                                price_val = int(price_num.group(1).replace(',', ''))
                                if 5 < price_val < 50000:
                                    data["realSum"] = price_val
                                    break
                    except:
                        continue
            except:
                pass
            
            # Method 2: Look for price in JSON data
            if not data["realSum"]:
                try:
                    price_json = re.search(r'"priceString"\s*:\s*"([^"]+)"', all_scripts)
                    if price_json:
                        price_str = price_json.group(1)
                        price_num = re.search(r'([\d,]+)', price_str)
                        if price_num:
                            data["realSum"] = int(price_num.group(1).replace(',', ''))
                except:
                    pass
            
            # Method 3: Search in page text
            if not data["realSum"]:
                price_patterns = [
                    r'[\$€£]\s*([\d,]+)\s*night',
                    r'[\$€£]\s*([\d,]+)\s*per\s*night',
                    r'[\d,]+\s*[\$€£]\s*night',
                ]
                for pattern in price_patterns:
                    price_m = re.search(pattern, page_text, re.IGNORECASE)
                    if price_m:
                        price_val = int(price_m.group(1).replace(',', ''))
                        if 5 < price_val < 50000:
                            data["realSum"] = price_val
                            break
            
            # ═══════════════════════════════════════════════
            # PERSON_CAPACITY / BEDROOMS / BEDS
            # ═══════════════════════════════════════════════
            guests_m = re.search(r'(\d+)\s*guest', page_text)
            if guests_m:
                data["person_capacity"] = int(guests_m.group(1))
            
            # ═══════════════════════════════════════════════
            # REVIEW COUNT
            # ═══════════════════════════════════════════════
            review_m = re.search(r'(\d+)\s*review', page_text)
            if review_m:
                data["review_count"] = int(review_m.group(1))
            
            # ═══════════════════════════════════════════════
            # RATINGS (guest_satisfaction_overall & cleanliness_rating)
            # ═══════════════════════════════════════════════
            # Try multiple methods for overall rating
            # Method 1: aria-label
            rating_elem = page.query_selector('span[aria-label*="rating"]')
            if rating_elem:
                rating_text = rating_elem.get_attribute('aria-label') or rating_elem.inner_text()
                rating_m = re.search(r'([\d.]+)', rating_text)
                if rating_m:
                    val = float(rating_m.group(1))
                    if val <= 5:
                        data["guest_satisfaction_overall"] = val
            
            # Method 2: Search in page text for "X.XX rating" or "rated X.XX"
            if not data["guest_satisfaction_overall"]:
                overall_patterns = [
                    r'([\d.]+)\s*rating',
                    r'rated\s*([\d.]+)',
                    r'rating[:\s]*([\d.]+)',
                    r'★\s*([\d.]+)',
                ]
                for pattern in overall_patterns:
                    rating_m = re.search(pattern, page_text, re.IGNORECASE)
                    if rating_m:
                        val = float(rating_m.group(1))
                        if 0 < val <= 5:
                            data["guest_satisfaction_overall"] = val
                            break
            
            # Cleanliness rating
            cleanliness_m = re.search(r'cleanliness\s*[:\s]*([\d.]+)', page_text)
            if cleanliness_m:
                val = float(cleanliness_m.group(1))
                if val <= 5:
                    data["cleanliness_rating"] = val
            
            # ═══════════════════════════════════════════════
            # AMENITIES (6 only: wifi, kitchen, AC, parking, tv, heating)
            # ═══════════════════════════════════════════════
            amenities_str = page_text
            
            data["wifi"] = any(w in amenities_str for w in ["wifi", "wi-fi", "internet"])
            data["kitchen"] = "kitchen" in amenities_str
            data["air_conditioning"] = any(w in amenities_str for w in ["air conditioning", "a/c", "ac", "cooling"])
            data["parking"] = any(w in amenities_str for w in ["parking", "garage"])
            data["tv"] = any(w in amenities_str for w in ["tv", "television", "hdtv"])
            data["heating"] = "heating" in amenities_str
            
            return data
            
        except Exception as e:
            self.log(f"Extraction error: {str(e)[:100]}")
            # Return partial data even if extraction fails
            return data if data.get("beds") or data.get("room_type") else None
    
    def scraping_complete(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_var.set(100)
        
        if self.scraped_data:
            self.export_btn.config(state=tk.NORMAL)
            self.results_var.set(f"Scraped {len(self.scraped_data)} listings successfully")
            self.log(f"\n{'='*50}")
            self.log(f"COMPLETE: {len(self.scraped_data)} listings scraped")
            self.log(f"{'='*50}")
            
            # Auto-save
            self.auto_save()
        else:
            self.results_var.set("No data was scraped")
        
        self.status_var.set("Ready")
    
    def auto_save(self):
        """Auto-save results to CSV"""
        # Get city name for filename
        city_name = self.scraped_data[0].get('city', 'data') if self.scraped_data else 'data'
        city_name = city_name.lower().replace(' ', '_')
        
        # CSV with clean naming
        csv_file = f"{city_name}_airbnb.csv"
        fieldnames = [
            "url",
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
            writer.writerows(self.scraped_data)
        
        self.log(f"Saved: {csv_file}")
    
    def auto_save_city(self, city_name, listings):
        """Save a specific city's listings to CSV"""
        city_name = city_name.lower().replace(' ', '_')
        
        # CSV with clean naming
        csv_file = f"{city_name}_airbnb.csv"
        fieldnames = [
            "url",
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
            writer.writerows(listings)
        
        self.log(f"Saved {len(listings)} listings to: {csv_file}")
    
    def export_csv(self):
        if not self.scraped_data:
            messagebox.showwarning("No Data", "No data to export")
            return
        
        city_name = self.scraped_data[0].get('city', 'data').lower().replace(' ', '_')
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{city_name}_airbnb.csv"
        )
        
        if file_path:
            fieldnames = list(self.scraped_data[0].keys())
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.scraped_data)
            
            self.log(f"Exported to: {file_path}")
            messagebox.showinfo("Export Complete", f"Data exported to:\n{file_path}")


def main():
    root = tk.Tk()
    
    # Modern Theme - Airbnb Colors
    style = ttk.Style()
    style.theme_use('clam')
    
    # Color scheme - White and Airbnb Pink
    bg_color = "white"
    accent_color = "#FF385C"
    text_color = "#222222"
    
    root.configure(bg=bg_color)
    
    # Configure styles
    style.configure("TFrame", background=bg_color)
    style.configure("TLabel", background=bg_color, foreground=text_color, font=('Segoe UI', 10))
    style.configure("TButton", font=('Segoe UI', 10), padding=6, background="#f7f7f7")
    style.configure("Accent.TButton", font=('Segoe UI', 10, 'bold'), background=accent_color, foreground="white")
    style.configure("TLabelframe", background=bg_color, foreground=text_color, borderwidth=1, relief="solid")
    style.configure("TLabelframe.Label", background=bg_color, foreground=text_color, font=('Segoe UI', 10, 'bold'))
    style.configure("TEntry", fieldbackground="white", borderwidth=1)
    style.configure("TRadiobutton", background=bg_color, foreground=text_color)
    
    # Map accent color
    style.map("Accent.TButton",
        foreground=[('active', 'white'), ('!disabled', 'white')],
        background=[('active', '#E31C5F'), ('!disabled', accent_color)])
    
    style.map("TButton",
        background=[('active', '#f0f0f0'), ('!disabled', '#f7f7f7')])
    
    app = AirbnbScraperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
