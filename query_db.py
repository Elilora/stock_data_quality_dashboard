import pandas as pd
from data_pipeline import ( tickers, engine, fetch_data,fetch_corporate_actions, run_quality_checks, load_from_db)


# Query the database using SQL
with engine.connect() as conn:

    # Query All quality issues by ticker
    query1 = pd.read_sql("""
        SELECT Ticker, Issue, COUNT(*) as Total
        FROM quality_issues
        GROUP BY Ticker, Issue
        ORDER BY Total DESC
    """, conn)
    print("\n--- Quality Issues Summary ---")
    print(query1)

    # Query Tickers with most issues
    query2 = pd.read_sql("""
        SELECT Ticker, SUM(Count) as Total_Issues
        FROM quality_issues
        GROUP BY Ticker
        ORDER BY Total_Issues DESC
    """, conn)
    print("\n--- Tickers Ranked by Issues ---")
    print(query2)

    # Query Corporate actions in last 6 months
    query3 = pd.read_sql("""
        SELECT Ticker, SUM(Dividends) as Total_Dividends,
               SUM("Stock Splits") as Total_Splits
        FROM corporate_actions
        GROUP BY Ticker
    """, conn)
    print("\n--- Corporate Actions Summary ---")
    print(query3)

    # Query flagged issues
    query4 = pd.read_sql("""
        SELECT * FROM quality_issues
        WHERE Count > 0
        ORDER BY Count DESC
    """, conn)
    print("\n--- Exception Report ---")
    print(query4)