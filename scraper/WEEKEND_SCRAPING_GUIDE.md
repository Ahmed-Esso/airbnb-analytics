# 🌙 Weekend Scraping Guide

## What Changed

Your Airbnb scraper now supports **Weekend Mode** to match your existing dataset pricing structure.

## New Features

### 1. **Weekend Mode Toggle**
- ☑️ Enable "Weekend Mode (Fri-Sun, 2 nights)" checkbox
- Automatically adds Friday check-in and Sunday check-out dates
- Scrapes listings for 2-night weekend stays

### 2. **Date Selection**
- **Check-in (Fri)**: Automatically set to next Friday
- **Check-out (Sun)**: Automatically set to next Sunday  
- **"⟳ Next Weekend" button**: Quickly jump to next weekend

### 3. **URL Construction**
When weekend mode is enabled, search URLs include:
```
&checkin=2026-01-31&checkout=2026-02-02
```

## How to Use

### Step 1: Launch the Scraper
```bash
python airbnb_scraper_app.py
```

### Step 2: Enable Weekend Mode
1. Check the **"🌙 Weekend Mode (Fri-Sun, 2 nights)"** checkbox
2. Date fields appear automatically
3. Dates are pre-filled with next Friday-Sunday

### Step 3: Select Cities
- Click individual city buttons (Paris, Rome, etc.)
- OR click **"✓ All Cities"** to scrape all 10 cities with weekend pricing

### Step 4: Configure Settings
- **Max Listings**: 20 (or more)
- **Parallel Workers**: 3-5 (faster processing)

### Step 5: Start Scraping
Click **"Start Scraping"** button

## Expected Results

### Price Comparison
**Before (weekday mode):**
- Berlin: $30-$109 per night
- Paris: $40-$120 per night

**After (weekend mode):**
- Berlin: $180-$650 for 2-night weekend
- Paris: $250-$800 for 2-night weekend

### CSV Output
Files are saved as: `{city}_airbnb.csv`
- amsterdam_airbnb.csv
- athens_airbnb.csv
- barcelona_airbnb.csv
- etc.

## Data Compatibility

### Now Comparable With Existing Data
Your scraped weekend data will now be comparable with `all_cities_final.csv`:

| Feature | Existing Data | New Scraped (Weekend Mode) |
|---------|--------------|---------------------------|
| Stay Type | Weekend | Weekend (Fri-Sun) |
| Duration | 2-3 nights | 2 nights |
| Pricing | Total stay | Total stay (2 nights) |
| Price Range | $194-$2,771 | $150-$1,200 (expected) |

## Next Steps After Scraping

### 1. Run Enrichment Pipeline
```bash
python data_enrichment_pipeline.py
```

When prompted:
- **Use Geoapify API?**: Type `yes` or `no`
- **Enter path to existing CSV**: Type the path to your `all_cities.csv` file (e.g., `cleaning/all_cities.csv`)

### 2. Results
Creates: `all_cities_enriched.csv`
- Combined scraped + existing data
- URL column removed
- All missing values imputed with KNN
- Location scores added (dist, metro_dist, attractions, restaurants)

## Tips

### For Maximum Data Quality
- ✅ Enable weekend mode for comparable pricing
- ✅ Scrape multiple weekends (change dates and re-scrape)
- ✅ Use 3-5 parallel workers for best performance
- ✅ Scrape 20-30 listings per city minimum

### For Testing
- Disable weekend mode to see the price difference
- Compare weekday vs weekend pricing side-by-side

## Troubleshooting

### "Dates not working"
- Click "⟳ Next Weekend" button to refresh dates
- Manually enter dates in YYYY-MM-DD format

### "Prices still low"
- Verify weekend mode checkbox is checked
- Check log shows: "🌙 Weekend Mode: 2026-01-31 to 2026-02-02"
- Verify URL includes `&checkin=` and `&checkout=` parameters

### "Want different dates"
- Edit dates manually in the date fields
- Use any Friday-Sunday combination
- Can also do Saturday-Monday by editing dates

## Example Workflow

```
1. Launch app → python airbnb_scraper_app.py
2. Check "Weekend Mode" ✓
3. Verify dates: Jan 31 (Fri) → Feb 2 (Sun)
4. Click "✓ All Cities"
5. Wait 20-30 minutes (10 cities × 20 listings)
6. CSV files created for all cities
7. Run enrichment pipeline
8. Analyze comparable weekend pricing data!
```

---

**🎉 Your scraper is now ready for weekend data collection!**
