# 📊 Financial Data Quality & Validation Dashboard

An automated financial data validation pipeline and interactive dashboard built with Python, yfinance, SQLite, and Streamlit. The project simulates the kind of data quality monitoring and exception reporting performed by Financial Data Analysts.

Tickers Monitored

`AAPL` `MSFT` `GOOGL` `JPM` `GS`

---

## 🔗 Live Dashboard
☁️ Deployed on Streamlit Cloud

This dashboard is deployed publicly using [Streamlit Community Cloud](https://streamlit.io/cloud).

👉 [View the live dashboard on Streamlit](https://tickerdataquality.streamlit.app)

> Note: The Streamlit deployment runs `dashboard.py` directly. Make sure `data_pipeline.py` is in the same repository so the imports work correctly. The SQLite database will be regenerated on each deployment using live Yahoo Finance data.

---

## 📌 Project Overview

This project ingests equity pricing data from Yahoo Finance, runs a suite of automated data quality checks, stores results in a structured SQLite database, and surfaces findings through an interactive dashboard.

It covers core Financial Data Analyst responsibilities including:

- **Data ingestion and validation** across multiple securities and sources
- **Exception reporting** — flagging anomalies, missing values, invalid prices, and trading day gaps
- **Corporate actions monitoring** — dividends and stock splits
- **SQL-based data storage and querying**
- **Interactive visualisation** of pricing trends, volume spikes, and quality metrics

---

## 🗂️ Project Structure

```
finance_data/
│
├── data_pipeline.py      # Core pipeline: fetch, validate, store
├── dashboard.py          # Streamlit dashboard (imports from pipeline)
├── finance_data.db       # SQLite database (auto-generated on first run)
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## ⚙️ Data Pipeline — `data_pipeline.py`

The pipeline handles all data logic independently of the dashboard:

| Function | Description |
|---|---|
| `fetch_data()` | Pulls 6 months of OHLCV data from Yahoo Finance |
| `fetch_corporate_actions()` | Retrieves dividend and stock split history |
| `check_data_quality()` | Runs validation checks on a single ticker |
| `run_quality_checks()` | Runs checks across all tickers and returns a report |
| `save_to_db()` | Persists price data, quality issues, and corporate actions to SQLite |
| `load_from_db()` | Loads all tables from SQLite for dashboard consumption |

### Data Quality Checks

| Check | Description |
|---|---|
| Missing Values | Null or NaN fields across any column |
| Duplicates | Duplicate rows in the dataset |
| Invalid Prices | Close price at zero or negative |
| Invalid High-Low | High price recorded below Low price |
| Zero Volume | Trading days with no recorded volume |
| Price Anomaly >10% | Single-day price moves exceeding 10% |
| Missing Trading Days | Business days absent from the dataset |

### 

---

## 📊 Dashboard — `dashboard.py`

The dashboard reads from the SQLite database and renders five interactive views:

### Overview
- KPI summary: total records validated, issues flagged, clean tickers
- Issues by type bar chart
- Latest prices table with daily returns

### Data Quality
- Issues per ticker bar chart
- Filterable exception report table
- Issue heatmap across tickers and issue types

### Price Analysis
- Interactive close price chart with anomaly flags
- Daily returns distribution with threshold lines
- Volume history with spike detection

### Corporate Actions
- Dividend and split summary table
- Per-ticker dividend history chart
- Raw corporate actions data

### Raw Data
- Filterable price data table with anomaly highlighting
- Descriptive statistics
- CSV download per ticker

---

## 🚀 How to Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/Elilora/finance-data-quality.git
cd finance-data-quality
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the data pipeline

This fetches data from Yahoo Finance, runs all quality checks, and populates the SQLite database:

```bash
python3 data_pipeline.py
```

### 4. Launch the dashboard

```bash
streamlit run dashboard.py
```

### 5. Refresh data

Use the **Refresh Data** button in the sidebar to re-run the pipeline and update the database without leaving the dashboard.

---

## 📦 Requirements

Create a `requirements.txt` file with the following:

```
yfinance
pandas
sqlalchemy
streamlit
matplotlib
```

OR Install all at once:

```bash
pip install -r requirements.txt
```

## 📈 Relevance to Financial Data Analysis

This project was built to demonstrate practical skills relevant to financial data operations roles, including:

- Cross-source data validation and exception reporting
- Corporate actions monitoring (dividends, splits)
- SQL-based data storage and querying
- Clear communication of data quality findings through dashboards
- Automated pipeline design with quality controls

---

