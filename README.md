# Airbnb Analytics — European Price Analysis & Prediction

An end-to-end data analytics project analyzing **51,000+ Airbnb listings** across **10 European cities**. The pipeline covers web scraping, data cleaning, star-schema data warehousing, statistical testing, interactive dashboards, and ML-powered price prediction.

![Dashboard Preview](dashboard/screenshots/page_1.jpg)

---

## Cities Covered

Amsterdam · Athens · Barcelona · Berlin · Budapest · Lisbon · London · Paris · Rome · Vienna

---

## Project Architecture

```
Scraping → Cleaning & Merging → Star Schema (SQL Server) → Statistical Analysis (R)
                                       ↓                            ↓
                                 Power BI Dashboard       ANOVA / MANOVA Tests
                                       ↓
                              Streamlit Web App + CatBoost Price Prediction
```

---

## Repository Structure

```
airbnb-analytics/
├── app/                        # Streamlit web application
│   ├── app.py                  # Main dashboard + AI price predictor
│   ├── airbnb_model.cbm        # Trained CatBoost regression model
│   ├── airbnb_symbol.svg       # App logo
│   └── data/
│       └── airbnb_listings_clean.csv   # Cleaned dataset (51K+ rows)
│
├── scraper/                    # Web scraping tools
│   ├── scraper_cli.py          # CLI scraper (Playwright + Chromium)
│   ├── scraper_gui.py          # GUI scraper (Tkinter + parallel workers)
│   ├── logo_base64.txt         # GUI app logo asset
│   └── WEEKEND_SCRAPING_GUIDE.md
│
├── cleaning/                   # Data cleaning & merging pipeline
│   ├── clean_and_merge.ipynb   # Jupyter notebook (KNN imputation, feature engineering)
│   ├── all_cities.csv          # Source dataset 1
│   └── scraped_data.csv        # Source dataset 2
│
├── schema/                     # Database & data warehouse
│   ├── star_schema.sql         # SQL Server DDL (star schema + BULK INSERT)
│   ├── analysis.sql            # 8 advanced analytical SQL queries
│   ├── hashing.ipynb           # Dimension ID generation (MD5 hashing)
│   ├── schema_diagram.png      # Star schema diagram
│   ├── erd.pdf                 # Entity-Relationship Diagram
│   ├── fact_table_output.csv   # Exported fact table
│   └── final_raw_with_ids.csv  # Dataset with dimension IDs
│
├── r_statistics/               # Statistical analysis
│   └── stat.R                  # ANOVA & MANOVA tests (price ~ room_type)
│
├── dashboard/                  # Power BI dashboard
│   ├── airbnb_dashboard.pbix   # Power BI file (4 pages)
│   └── screenshots/            # Dashboard page exports
│
├── requirements.txt            # Python dependencies
├── .gitattributes              # Git LFS tracking rules
└── .gitignore
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Scraping** | Python, Playwright, Chromium, Tkinter |
| **Cleaning** | Pandas, NumPy, Scikit-learn (KNN Imputer) |
| **Database** | SQL Server, Star Schema (5 dimensions + 1 fact table) |
| **Statistics** | R, dplyr (ANOVA, MANOVA, Tukey HSD) |
| **Dashboard** | Power BI |
| **ML Model** | CatBoost Regressor (log-price prediction) |
| **Web App** | Streamlit, Plotly |

---

## Features

### Streamlit Web App
- **Interactive Map** — Geographic view of listings with click-to-predict
- **Dynamic Filters** — City, room type, price range, capacity, rating, superhost, weekend
- **KPI Dashboard** — Listing count, average price, average rating
- **6 Interactive Charts** — Satisfaction gauge, room type distribution, price box plots, weekend comparison, superhost breakdown, capacity analysis
- **AI Price Predictor** — Form-based price estimation using a trained CatBoost model

### Data Pipeline
- Web scraping with headless Chromium (supports 10 cities, weekend mode)
- KNN-based imputation for missing values (amenities, bedrooms, beds)
- Feature engineering: binary flags, distance metrics, weekend indicators
- Star schema with MD5-hashed dimension IDs

### Statistical Analysis
- **ANOVA**: Price differences across room types (with Tukey HSD post-hoc)
- **MANOVA**: Multivariate test on price, satisfaction, and cleanliness by room type

---

## Quick Start

### Prerequisites
- Python 3.10+
- Git LFS (`git lfs install`)

### Installation

```bash
# Clone the repository
git clone https://github.com/Ahmed-Esso/airbnb-analytics.git
cd airbnb-analytics

# Create virtual environment
python -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run the Streamlit App

```bash
streamlit run app/app.py
```

The app will open at `http://localhost:8501`.

---

## Streamlit Cloud Deployment

This project is ready for [Streamlit Community Cloud](https://share.streamlit.io):

1. Push this repo to GitHub (public)
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **"New app"** and select this repository
4. Set **Main file path** to `app/app.py`
5. Click **Deploy**

> **Note:** Git LFS files are supported on Streamlit Cloud. The `requirements.txt` at the repo root is automatically detected.

---

## Dashboard Preview

| Page 1 | Page 2 |
|--------|--------|
| ![Page 1](dashboard/screenshots/page_1.jpg) | ![Page 2](dashboard/screenshots/page_2.jpg) |

| Page 3 | Page 4 |
|--------|--------|
| ![Page 3](dashboard/screenshots/page_3.jpg) | ![Page 4](dashboard/screenshots/page_4.jpg) |

---

## SQL Server Setup (Optional)

### Star Schema

![Star Schema Diagram](schema/schema_diagram.png)

To load data into a local SQL Server instance:

1. Open `schema/star_schema.sql` in SSMS
2. Update the `BULK INSERT` path to point to your local `schema/final_raw_with_ids.csv`
3. Execute the script to create the `Airbnb_DW` database
4. Run `schema/analysis.sql` for advanced analytics queries

---

## License

This project is for educational and portfolio purposes.
