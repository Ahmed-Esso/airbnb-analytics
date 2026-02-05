<div align="center">

# 🏠 Airbnb Analytics
### European Price Analysis & ML Prediction

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://share.streamlit.io)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![R](https://img.shields.io/badge/R-276DC3?style=for-the-badge&logo=r&logoColor=white)](https://www.r-project.org)
[![SQL Server](https://img.shields.io/badge/SQL_Server-CC2927?style=for-the-badge&logo=microsoftsqlserver&logoColor=white)](https://www.microsoft.com/sql-server)
[![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com)

An end-to-end data analytics project analyzing **51,000+ Airbnb listings** across **10 European cities**.  
From web scraping to ML-powered price prediction — covering ETL, data warehousing, statistical testing, and interactive dashboards.

**Amsterdam · Athens · Barcelona · Berlin · Budapest · Lisbon · London · Paris · Rome · Vienna**

</div>

---

![Dashboard Preview](dashboard/screenshots/page_1.jpg)

---

## 📋 Table of Contents

- [Project Architecture](#-project-architecture)
- [Repository Structure](#-repository-structure)
- [Detailed File Descriptions](#-detailed-file-descriptions)
- [Tech Stack](#-tech-stack)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Streamlit Cloud Deployment](#-streamlit-cloud-deployment)
- [Dashboard Gallery](#-dashboard-gallery)
- [Star Schema & Database](#-star-schema--database)
- [License](#-license)

---

## 🏗 Project Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  🕷 Scraper  │────▶│  🧹 Cleaning &   │────▶│  🗃 Star Schema     │
│  (Playwright)│     │  Merging (Pandas) │     │  (SQL Server DW)    │
└─────────────┘     └──────────────────┘     └────────┬────────────┘
                                                       │
                           ┌───────────────────────────┼───────────────────┐
                           ▼                           ▼                   ▼
                    ┌─────────────┐          ┌──────────────┐    ┌──────────────┐
                    │  📊 Power BI │          │  📈 R Stats   │    │  🤖 Streamlit │
                    │  Dashboard   │          │  ANOVA/MANOVA │    │  + CatBoost   │
                    └─────────────┘          └──────────────┘    └──────────────┘
```

> **Pipeline flow:** Scrape raw listings → Clean & merge datasets → Load into star schema → Analyze with SQL, R, and Power BI → Predict prices with CatBoost via Streamlit

---

## 📁 Repository Structure

```
airbnb-analytics/
│
├── 📂 app/                          # Streamlit web application
│   ├── app.py                       # Main app (dashboard + AI predictor)
│   ├── airbnb_model.cbm             # Trained CatBoost model
│   ├── airbnb_symbol.svg            # App intro logo
│   └── data/
│       └── airbnb_listings_clean.csv # Final cleaned dataset
│
├── 📂 scraper/                      # Web scraping tools
│   ├── scraper_cli.py               # Command-line scraper
│   ├── scraper_gui.py               # GUI scraper with Tkinter
│   ├── logo_base64.txt              # GUI logo (base64 encoded)
│   └── WEEKEND_SCRAPING_GUIDE.md    # Weekend mode documentation
│
├── 📂 cleaning/                     # Data cleaning pipeline
│   ├── clean_and_merge.ipynb        # Cleaning notebook
│   ├── all_cities.csv               # Source dataset 1 (existing listings)
│   └── scraped_data.csv             # Source dataset 2 (scraped from Airbnb)
│
├── 📂 schema/                       # Database & data warehouse
│   ├── star_schema.sql              # Database DDL (tables + bulk insert)
│   ├── analysis.sql                 # 9 advanced analytical queries
│   ├── hashing.ipynb                # Dimension ID generation notebook
│   ├── schema_diagram.png           # Star schema visual diagram
│   ├── erd.pdf                      # Entity-Relationship Diagram
│   ├── fact_table_output.csv        # Exported fact table
│   └── final_raw_with_ids.csv       # Full dataset with dimension IDs
│
├── 📂 r_statistics/                 # Statistical analysis
│   └── stat.R                       # ANOVA & MANOVA tests
│
├── 📂 dashboard/                    # Power BI dashboard
│   ├── airbnb_dashboard.pbix        # Power BI file (4 pages)
│   └── screenshots/                 # Exported dashboard images
│       ├── page_1.jpg               # Overview page
│       ├── page_2.jpg               # City comparison page
│       ├── page_3.jpg               # Pricing analysis page
│       └── page_4.jpg               # Host & amenity insights page
│
├── requirements.txt                 # Python dependencies
├── .gitattributes                   # Git LFS tracking rules
├── .gitignore                       # Ignored files & folders
└── README.md                        # This file
```

---

## 📖 Detailed File Descriptions

### 🤖 `app/` — Streamlit Web Application

| File | Description |
|------|-------------|
| **`app.py`** | Full-featured Streamlit dashboard (573 lines). Includes an animated intro screen, sidebar with 7 interactive filters (city, room type, price range, guest capacity, rating, superhost, weekend), 3 KPI cards, an interactive Plotly map with click-to-predict, 6 analytical charts (satisfaction gauge, room type pie, price box plot, weekend comparison bar, superhost donut, capacity bar), and an AI Smart Predictor form that uses CatBoost to estimate nightly prices. |
| **`airbnb_model.cbm`** | Trained CatBoost Regressor model. Predicts `log(price)` from features like city, room type, guest capacity, cleanliness rating, distance from center, and weekend flag. The app applies `np.expm1()` to convert predictions back to dollar amounts. |
| **`airbnb_symbol.svg`** | Airbnb logo SVG used in the app's 3-second intro animation (fade-in + scale effect). |
| **`data/airbnb_listings_clean.csv`** | The final cleaned dataset with 51,000+ rows and 30+ columns. Each row is a single Airbnb listing with price, location, amenities, ratings, and derived features. This is the single source of truth for the app. |

### 🕷 `scraper/` — Web Scraping Tools

| File | Description |
|------|-------------|
| **`scraper_cli.py`** | Command-line Playwright scraper (661 lines). Launches headless Chromium, navigates Airbnb search pages for a given city, collects listing URLs, then visits each listing to extract: price per night, room type, guest capacity, amenities (wifi, kitchen, AC, parking, TV, heating), latitude/longitude, ratings, superhost status, and more. Outputs CSV + JSON files. Handles anti-bot detection with random delays and stealth mode. |
| **`scraper_gui.py`** | Full Tkinter GUI wrapper (1,270 lines) around the scraper engine. Features: mode selection (city search / direct URL / single listing), quick-select buttons for all 10 cities, parallel scraping with `ThreadPoolExecutor`, weekend mode toggle, real-time progress bar, scrollable log window, auto-save per city, and export to CSV. Includes a branded UI with the embedded logo. |
| **`logo_base64.txt`** | Base64-encoded PNG logo used by the GUI scraper. Loaded at runtime to avoid external image dependencies. |
| **`WEEKEND_SCRAPING_GUIDE.md`** | Documentation for the weekend scraping mode — explains how to scrape weekend-specific pricing data and merge it with existing datasets using the enrichment pipeline. |

### 🧹 `cleaning/` — Data Cleaning & Merging

| File | Description |
|------|-------------|
| **`clean_and_merge.ipynb`** | Jupyter notebook (27 cells) that runs the full data cleaning pipeline: **(1)** Loads `all_cities.csv` and `scraped_data.csv`, **(2)** normalizes columns (converts cleanliness from 10-scale to 5-scale, renames lat/lng), **(3)** creates binary flags (`room_shared`, `room_private`), **(4)** extracts city from host location and filters to the 10 target cities, **(5)** engineers features: weekend/weekday indicator, amenity booleans (wifi, kitchen, AC, parking, TV, heating), **(6)** merges both datasets via `pd.concat`, **(7)** applies KNN imputation (k=3, distance-weighted) in batches of 100 rows for missing amenities, bedrooms, and beds, **(8)** outputs the final clean CSV. Uses `tqdm` for progress tracking. |
| **`all_cities.csv`** | Source dataset 1 — pre-existing Airbnb listing data covering all 10 cities with columns like `realSum`, `room_type`, `person_capacity`, `cleanliness_rating`, `guest_satisfaction_overall`, `dist` (distance to center), `metro_dist`, and attraction/restaurant indices. |
| **`scraped_data.csv`** | Source dataset 2 (254 MB) — raw data scraped from Airbnb/Inside Airbnb. Contains listing prices, coordinates, room details, and amenity flags. Merged with dataset 1 to create the comprehensive final dataset. |

### 🗃 `schema/` — Star Schema & SQL Analytics

| File | Description |
|------|-------------|
| **`star_schema.sql`** | SQL Server DDL script that creates the `Airbnb_DW` data warehouse. Defines **5 dimension tables** (`Dim_Location`, `Dim_Host`, `Dim_Room_Type`, `Dim_Amenities`, `Dim_Day`) and **1 fact table** (`Fact_Listings`) with foreign key constraints. Includes a staging `Raw_Data` table and `BULK INSERT` command to load CSV data. Also contains `INSERT INTO` statements to populate dimensions from the staging table. |
| **`analysis.sql`** | 9 advanced analytical SQL queries (849 lines) that run against the star schema: |
| | **1. ListingScore** — Scores each listing against city/room-type benchmarks |
| | **2. SegmentDashboard** — Aggregates metrics by city × room-type segments |
| | **3. BestDeals / WorstDeals** — Finds underpriced and overpriced listings |
| | **4. AccessibilitySegment** — Compares metro-accessible vs center-close listings |
| | **5. AmenityTier** — Classifies listings as Basic / Comfort / Full amenity tiers |
| | **6. InsightColumns AllInOne** — Combines all analytical columns into one view |
| | **7. FeatureImpactRadar** — Measures price premium/discount per feature |
| | **8. GeoDemandHotspots** — Geographic grid analysis for high-demand areas |
| | **9. StrategyScoring** — Scores weekend + amenity pricing strategies |
| **`hashing.ipynb`** | Jupyter notebook (19 cells) that generates unique dimension IDs using MD5 hashing. For each dimension table, it extracts unique combinations of attributes, hashes them into integer IDs, merges all IDs back to the original dataset, cleans up duplicate columns from the merge, and exports the final dataset with all foreign keys. |
| **`schema_diagram.png`** | Visual diagram of the star schema showing the relationships between the fact table and all 5 dimensions. |
| **`erd.pdf`** | Entity-Relationship Diagram (PDF) documenting the full database design. |
| **`fact_table_output.csv`** | Exported fact table containing listing measures (price, capacity, bedrooms, beds, ratings) linked to dimension IDs. |
| **`final_raw_with_ids.csv`** | Complete dataset (73 MB) with all original columns plus the 5 generated dimension IDs (`location_id`, `host_id`, `room_type_id`, `amenity_id`, `day_id`). Used by R statistics and SQL BULK INSERT. |

### 📈 `r_statistics/` — Statistical Analysis

| File | Description |
|------|-------------|
| **`stat.R`** | R script (190 lines) performing two key statistical tests: |
| | **ANOVA** — One-way analysis of variance testing whether mean price differs significantly across room types (Entire home, Private room, Shared room). Includes Tukey HSD post-hoc test to identify which pairs differ. Produces boxplots and error bar charts. |
| | **MANOVA** — Multivariate analysis testing whether room type simultaneously affects price, guest satisfaction, and cleanliness rating. Uses Wilks' Lambda test statistic. Produces scatter pair plots and grouped bar charts comparing means across all three variables. |
| | Uses `dplyr` for data aggregation (group means, standard errors). All visualizations use Airbnb brand colors (`#FF5A5F`, `#FBB6B8`, `#C81E1E`). |

### 📊 `dashboard/` — Power BI Dashboard

| File | Description |
|------|-------------|
| **`airbnb_dashboard.pbix`** | Power BI dashboard with 4 interactive pages. Connects to the star schema data and provides drill-down visualizations for pricing trends, city comparisons, host performance, and amenity impact analysis. |
| **`screenshots/page_1-4.jpg`** | Exported images of each dashboard page for preview in this README (see [Dashboard Gallery](#-dashboard-gallery) below). |

### 📄 Root Files

| File | Description |
|------|-------------|
| **`requirements.txt`** | Python dependencies for the Streamlit app: `streamlit`, `pandas`, `plotly`, `numpy`, `catboost`. Placed at the repo root so Streamlit Cloud auto-detects it. |
| **`.gitattributes`** | Git LFS tracking rules — all `.csv`, `.cbm`, and `.pbix` files are stored in Git Large File Storage to stay under GitHub's 100 MB per-file limit. |
| **`.gitignore`** | Excludes virtual environments, `__pycache__`, R session files, IDE configs, OS files, backup files, and scraper runtime outputs from version control. |

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Scraping** | Python, Playwright, Chromium | Headless browser automation for data collection |
| **Data Cleaning** | Pandas, NumPy, Scikit-learn | Merging, normalization, KNN imputation |
| **Database** | SQL Server | Star schema data warehouse (5 dim + 1 fact) |
| **Statistics** | R, dplyr | ANOVA, MANOVA, Tukey HSD post-hoc tests |
| **Dashboard** | Power BI | 4-page interactive business intelligence dashboard |
| **ML Model** | CatBoost Regressor | Log-price prediction with gradient boosting |
| **Web App** | Streamlit, Plotly | Interactive dashboard + real-time price predictor |
| **Version Control** | Git, Git LFS | Large file storage for CSVs, model, and Power BI |

---

## ✨ Features

### Streamlit Web App
| Feature | Details |
|---------|---------|
| 🗺 **Interactive Map** | Plotly scatter map of 1,500 sampled listings with color-coded prices. Click any point to trigger an AI price prediction for that location. |
| 🎛 **7 Sidebar Filters** | City, room type, price range, guest capacity, minimum rating, superhost status, and day type (weekend/weekday). All apply in real-time. |
| 📊 **3 KPI Cards** | Total listings count, average nightly price, and average guest satisfaction — all responsive to active filters. |
| 📈 **6 Charts** | Satisfaction gauge, room type pie chart, price box plot by room type, weekend vs weekday bar chart, superhost donut chart, and price by guest capacity. |
| 🤖 **AI Predictor** | Form-based interface: select city, room type, capacity, cleanliness, distance, and weekend — get an instant CatBoost price estimate. |
| 🎬 **Intro Animation** | 3-second branded splash screen with SVG logo fade-in on first load. |

### Data Pipeline
| Stage | Details |
|-------|---------|
| 🕷 **Scraping** | Headless Chromium navigates Airbnb, extracts listing data with anti-detection (random delays, stealth mode). Supports batch city scraping and weekend mode. |
| 🧹 **Cleaning** | Normalizes two heterogeneous datasets, engineers 10+ features, applies batched KNN imputation (k=3, distance-weighted) for missing values. |
| 🗃 **Warehousing** | MD5-hashed dimension keys, star schema with proper foreign key constraints, and 9 advanced analytical queries. |
| 📈 **Statistics** | ANOVA confirms significant price differences across room types; MANOVA reveals multivariate effects on price + satisfaction + cleanliness. |

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Git LFS** — required for large file downloads

### Installation

```bash
# 1. Install Git LFS (if not already installed)
git lfs install

# 2. Clone the repository (LFS files download automatically)
git clone https://github.com/Ahmed-Esso/airbnb-analytics.git
cd airbnb-analytics

# 3. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Linux / Mac

# 4. Install dependencies
pip install -r requirements.txt
```

### Run the Streamlit App

```bash
streamlit run app/app.py
```

The app will open at **http://localhost:8501** 🎉

### Run the Scraper (Optional)

```bash
# Install Playwright browsers first
pip install playwright
playwright install chromium

# CLI scraper
python scraper/scraper_cli.py

# GUI scraper
python scraper/scraper_gui.py
```

### Run R Statistics (Optional)

```r
# In RStudio or R console, set the working directory to the repo root
setwd("path/to/airbnb-analytics")
source("r_statistics/stat.R")
```

---

## ☁ Streamlit Cloud Deployment

This project is **ready for one-click deployment** on [Streamlit Community Cloud](https://share.streamlit.io):

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
2. Click **"New app"**
3. Select the `airbnb-analytics` repository
4. Set **Main file path** to `app/app.py`
5. Click **Deploy** 🚀

> **Note:** Streamlit Cloud supports Git LFS and automatically detects `requirements.txt` at the repo root. No additional configuration needed.

---

## 📊 Dashboard Gallery

<table>
  <tr>
    <td><strong>Page 1 — Overview</strong></td>
    <td><strong>Page 2 — City Comparison</strong></td>
  </tr>
  <tr>
    <td><img src="dashboard/screenshots/page_1.jpg" alt="Dashboard Page 1" width="100%"></td>
    <td><img src="dashboard/screenshots/page_2.jpg" alt="Dashboard Page 2" width="100%"></td>
  </tr>
  <tr>
    <td><strong>Page 3 — Pricing Analysis</strong></td>
    <td><strong>Page 4 — Host & Amenity Insights</strong></td>
  </tr>
  <tr>
    <td><img src="dashboard/screenshots/page_3.jpg" alt="Dashboard Page 3" width="100%"></td>
    <td><img src="dashboard/screenshots/page_4.jpg" alt="Dashboard Page 4" width="100%"></td>
  </tr>
</table>

---

## 🗃 Star Schema & Database

### Schema Diagram

![Star Schema Diagram](schema/schema_diagram.png)

The data warehouse (`Airbnb_DW`) uses a **star schema** design with:

| Table | Type | Key Columns |
|-------|------|-------------|
| `Fact_Listings` | Fact | `realSum`, `person_capacity`, `bedrooms`, `beds`, `cleanliness_rating`, `guest_satisfaction_overall`, `dist`, `metro_dist`, `attr_index`, `rest_index` |
| `Dim_Location` | Dimension | `city`, `country`, `latitude`, `longitude` |
| `Dim_Host` | Dimension | `host_is_superhost` |
| `Dim_Room_Type` | Dimension | `room_type`, `room_shared`, `room_private` |
| `Dim_Amenities` | Dimension | `wifi`, `kitchen`, `air_conditioning`, `parking`, `tv`, `heating` |
| `Dim_Day` | Dimension | `day_type`, `is_weekend`, `biz`, `multi` |

### SQL Server Setup (Optional)

1. Open `schema/star_schema.sql` in SQL Server Management Studio (SSMS)
2. Update the `BULK INSERT` path to your local `schema/final_raw_with_ids.csv`
3. Execute the script to create the `Airbnb_DW` database and populate all tables
4. Run `schema/analysis.sql` for the 9 advanced analytical queries

---

## 📜 License

This project is for **educational and portfolio purposes**.

---

## 👥 Team Members

| Name | GitHub |
|------|--------|
| **Ahmed Essam** | [@Ahmed-Esso](https://github.com/Ahmed-Esso) |
| **Mayar Hany** | [@Mayar-hany-2005](https://github.com/Mayar-hany-2005) |
| **Ziad Abdeen** | |
| **Seif Nour** | |

---

<div align="center">

**Built with ❤️ by the Airbnb Analytics Team**

</div>
