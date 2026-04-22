import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine

# Initialise ticker and time period
tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "GS"]


# Create a database engine 
db_path = "finance_data.db"
engine = create_engine(f"sqlite:///{db_path}")



def fetch_data(tickers=tickers, period="6mo"):
    data = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)[["Close", "Volume", "Open", "High", "Low"]]
        df["Daily_Return"] = df["Close"].pct_change()
        data[ticker] = df
    return data



def fetch_corporate_actions(tickers=tickers):
    # Store corporate actions in SQL
    actions = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        actions[ticker] = stock.actions
    return actions

def check_data_quality(data, ticker):

    report = []
    # check for missing values
    missing = data.isnull().sum().sum()
    if missing>0:
        report.append({"Ticker":ticker, "Issue":"Missing Values", "Count":missing})
    
    # check for duplicates
    duplicates = data.duplicated().sum()
    if duplicates>0:
        report.append({"Ticker":ticker, "Issue":"Duplicates", "Count":duplicates})
    
    # check invalid prices (ranging from zero to negative)
    invalid_prices = data[data["Close"]<=0]
    if len(invalid_prices)>0:
        report.append({"Ticker":ticker, "Issue":"Invalid Prices", "Count":len(invalid_prices)})

    # check for high and low price consistency
    invalid_high_low = data[data["High"]<data["Low"]]
    if len(invalid_high_low)>0:
        report.append({"Ticker":ticker, "Issue":"Invalid High-Low", "Count":len(invalid_high_low)})

    # check for zero volume
    invalid_volume = data[data["Volume"]==0]
    if len(invalid_volume)>0:
        report.append({"Ticker":ticker, "Issue":"Invalid Volume", "Count":len(invalid_volume)})

    # Daily return anomalies — moves greater than 10%
    anomalies = data[abs(data["Daily_Return"]) > 0.10]
    if len(anomalies) > 0:
        report.append({"Ticker": ticker, "Issue": "Price Anomaly >10%", "Count": len(anomalies)})
    
    # Gaps in trading days — missing dates
    date_range = pd.date_range(start=data.index.min().normalize(), end=data.index.max().normalize(), freq="B")
    missing_dates = date_range.difference(data.index.normalize())
    if len(missing_dates) > 0:
        report.append({"Ticker": ticker, "Issue": "Missing Trading Days", "Count": len(missing_dates)})

    return report


def run_quality_checks(data, tickers=tickers):
    all_issues = []
    for ticker in tickers:
        issues = check_data_quality(data[ticker], ticker)
        all_issues.extend(issues)
    return pd.DataFrame(all_issues) if all_issues else pd.DataFrame( columns=["Ticker", "Issue", "Count"])

def save_to_db(data, quality_report, corporate_actions, tickers=tickers):
    #Save the data to the SQL database
    for ticker in tickers:
        df = data[ticker].copy()
        df["Ticker"] = ticker
        df.to_sql("price_data", engine, if_exists="append", index=True)

    # Store quality issues in SQL
    if not quality_report.empty:
        quality_report.to_sql("quality_issues", engine, if_exists="replace", index=False)
        print("Quality issues stored successfully")
    else:
        print("No quality issues found")

    for ticker in tickers:
        actions = corporate_actions[ticker].copy()
        if not actions.empty:
            actions["Ticker"] = ticker
            actions.to_sql("corporate_actions", engine, if_exists="append", index=True)

def load_from_db():
    with engine.connect() as conn:
        price_data = pd.read_sql("SELECT * FROM price_data", conn)
        try:
            quality_issues = pd.read_sql("SELECT * FROM quality_issues", conn)
        except Exception:
            quality_issues = pd.DataFrame(columns=["Ticker", "Issue", "Count"])
        try:
            corporate_actions = pd.read_sql("SELECT * FROM corporate_actions", conn)
        except Exception:
            corporate_actions = pd.DataFrame()
    return price_data, quality_issues, corporate_actions

if __name__ == "__main__":
    print("Fetching data...")
    data = fetch_data()
    corporate_actions = fetch_corporate_actions()
    quality_report = run_quality_checks(data)
    save_to_db(data, quality_report, corporate_actions)
    print("Pipeline complete. Database updated.")
    print(quality_report)




