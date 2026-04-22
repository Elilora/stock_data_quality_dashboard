# dashboard.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from data_pipeline import ( tickers, engine, fetch_data,fetch_corporate_actions, run_quality_checks, load_from_db)

st.set_page_config(page_title="Financial Data Quality Dashboard",page_icon="📊",layout="wide")

#Load from DB or refresh
st.sidebar.title("📊 Navigation")
refresh = st.sidebar.button("🔄 Refresh Data")

if refresh:
    with st.spinner("Fetching latest market data..."):
        data = fetch_data()
        corporate_actions = fetch_corporate_actions()
        quality_report = run_quality_checks(data)
    st.sidebar.success("Data refreshed successfully")
else:
    with st.spinner("Loading from database..."):
        price_data_raw, quality_report, ca_raw = load_from_db()

        # Reconstruct data dict from DB
        data = {}
        for ticker in tickers:
            df = price_data_raw[price_data_raw["Ticker"] == ticker].copy()
            df = df.drop(columns=["Ticker"])
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")
            if "Daily_Return" not in df.columns:
                df["Daily_Return"] = df["Close"].pct_change()
            data[ticker] = df

        # Reconstruct corporate actions dict from DB
        corporate_actions = {}
        for ticker in tickers:
            if not ca_raw.empty and "Ticker" in ca_raw.columns:
                ca = ca_raw[ca_raw["Ticker"] == ticker].copy()
                ca = ca.drop(columns=["Ticker"])
                corporate_actions[ticker] = ca
            else:
                corporate_actions[ticker] = pd.DataFrame()


# Sidebar navigation
page = st.sidebar.radio(
    "Select a view",
    ["Overview", "Data Quality", "Price Analysis", "Corporate Actions", "Raw Data"])

st.sidebar.markdown("---")
st.sidebar.markdown("**Tickers monitored:**")
for t in tickers:
    st.sidebar.markdown(f"- {t}")
st.sidebar.markdown("**Period:** 6 months")
st.sidebar.markdown("**Source:** Yahoo Finance via SQLite DB")




# PAGE 1 — OVERVIE
if page == "Overview":
    st.title("📊 Financial Data Quality Dashboard")
    st.markdown("Automated validation pipeline for equity pricing and reference data.")
    st.markdown("---")

    total_records = sum(len(data[t]) for t in tickers)
    total_issues = quality_report["Count"].sum() if not quality_report.empty else 0
    tickers_with_issues = quality_report["Ticker"].nunique() if not quality_report.empty else 0
    clean_tickers = len(tickers) - tickers_with_issues

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records Validated", f"{total_records:,}")
    col2.metric("Total Issues Flagged", f"{int(total_issues):,}")
    col3.metric("Tickers with Issues", f"{tickers_with_issues} / {len(tickers)}")
    col4.metric("Clean Tickers", f"{clean_tickers}")

    st.markdown("---")

    if not quality_report.empty:
        st.subheader("Issues by Type")
        issue_summary = quality_report.groupby("Issue")["Count"].sum().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(10, 4))
        bars = ax.bar(issue_summary.index, issue_summary.values, color="#1f77b4", edgecolor="white")
        ax.set_xlabel("Issue Type")
        ax.set_ylabel("Count")
        ax.set_title("Data Quality Issues by Type")
        plt.xticks(rotation=30, ha="right")
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(int(bar.get_height())), ha="center", va="bottom", fontsize=9)
        st.pyplot(fig)
    else:
        st.success("No data quality issues found.")

    st.markdown("---")
    st.subheader("Latest Prices")
    latest = []
    for ticker in tickers:
        df = data[ticker]
        latest.append({
            "Ticker": ticker,
            "Latest Close ($)": round(df["Close"].iloc[-1], 2),
            "1D Return (%)": round(df["Daily_Return"].iloc[-1] * 100, 2),
            "6M High ($)": round(df["Close"].max(), 2),
            "6M Low ($)": round(df["Close"].min(), 2),
            "Avg Volume": f"{int(df['Volume'].mean()):,}"
        })
    st.dataframe(pd.DataFrame(latest), use_container_width=True)


# PAGE 2 — DATA QUALITY
elif page == "Data Quality":
    st.title("🔍 Data Quality Report")
    st.markdown("---")

    if quality_report.empty:
        st.success("No data quality issues detected.")
    else:
        st.subheader("Total Issues per Ticker")
        ticker_summary = quality_report.groupby("Ticker")["Count"].sum().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(8, 4))
        colors = ["#d62728" if v == ticker_summary.max() else "#1f77b4" for v in ticker_summary.values]
        bars = ax.bar(ticker_summary.index, ticker_summary.values, color=colors, edgecolor="white")
        ax.set_xlabel("Ticker")
        ax.set_ylabel("Total Issues")
        ax.set_title("Data Quality Issues by Ticker")
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    str(int(bar.get_height())), ha="center", va="bottom", fontsize=10)
        st.pyplot(fig)

        st.markdown("---")
        st.subheader("Exception Report")
        ticker_filter = st.multiselect("Filter by ticker", options=tickers, default=tickers)
        filtered = quality_report[quality_report["Ticker"].isin(ticker_filter)]
        st.dataframe(filtered.sort_values("Count", ascending=False), use_container_width=True)

        st.markdown("---")
        st.subheader("Issue Heatmap")
        pivot = quality_report.pivot_table(index="Ticker", columns="Issue", values="Count", fill_value=0)
        fig, ax = plt.subplots(figsize=(12, 4))
        im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns, rotation=30, ha="right")
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        plt.colorbar(im, ax=ax, label="Count")
        ax.set_title("Issue Heatmap")
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                ax.text(j, i, str(int(pivot.values[i, j])),
                        ha="center", va="center", fontsize=9)
        st.pyplot(fig)

# PAGE 3 — PRICE ANALYSIS
elif page == "Price Analysis":
    st.title("📈 Price Analysis")
    st.markdown("---")

    selected_ticker = st.selectbox("Select Ticker", tickers)
    df = data[selected_ticker]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Price", f"${df['Close'].iloc[-1]:.2f}")
        st.metric("6M High", f"${df['Close'].max():.2f}")
    with col2:
        daily_return = df["Daily_Return"].iloc[-1] * 100
        st.metric("Latest Daily Return", f"{daily_return:.2f}%", delta=f"{daily_return:.2f}%")
        st.metric("6M Low", f"${df['Close'].min():.2f}")

    st.markdown("---")
    anomalies = df[abs(df["Daily_Return"]) > 0.10]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df["Close"], color="#1f77b4", linewidth=1.5, label="Close Price")
    if not anomalies.empty:
        ax.scatter(anomalies.index, anomalies["Close"], color="red", zorder=5, s=80, label="Anomaly >10%")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    ax.set_title(f"{selected_ticker} Close Price with Anomaly Flags")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.xticks(rotation=30)
    st.pyplot(fig)

    st.markdown("---")
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.hist(df["Daily_Return"].dropna(), bins=40, color="#1f77b4", edgecolor="white", alpha=0.8)
    ax2.axvline(x=0.10, color="red", linestyle="--", label="+10% threshold")
    ax2.axvline(x=-0.10, color="red", linestyle="--", label="-10% threshold")
    ax2.set_xlabel("Daily Return")
    ax2.set_ylabel("Frequency")
    ax2.set_title(f"{selected_ticker} Daily Returns Distribution")
    ax2.legend()
    st.pyplot(fig2)

    st.markdown("---")
    avg_vol = df["Volume"].mean()
    vol_spikes = df[df["Volume"] > avg_vol * 5]
    fig3, ax3 = plt.subplots(figsize=(12, 3))
    ax3.bar(df.index, df["Volume"], color="#aec7e8", width=1, label="Volume")
    if not vol_spikes.empty:
        ax3.bar(vol_spikes.index, vol_spikes["Volume"], color="red", width=1, label="Volume Spike")
    ax3.axhline(y=avg_vol, color="orange", linestyle="--", label="Average Volume")
    ax3.set_xlabel("Date")
    ax3.set_ylabel("Volume")
    ax3.set_title(f"{selected_ticker} Trading Volume")
    ax3.legend()
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.xticks(rotation=30)
    st.pyplot(fig3)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — CORPORATE ACTIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Corporate Actions":
    st.title("🏢 Corporate Actions")
    st.markdown("---")

    summary = []
    for ticker in tickers:
        actions = corporate_actions[ticker]
        if not actions.empty and "Dividends" in actions.columns:
            total_div = actions["Dividends"].sum()
            divs = actions[actions["Dividends"] > 0]
            last_div = divs["Dividends"].iloc[-1] if not divs.empty else 0
            total_splits = actions["Stock Splits"].sum() if "Stock Splits" in actions.columns else 0
            summary.append({
                "Ticker": ticker,
                "Total Dividends ($)": round(total_div, 4),
                "Last Dividend ($)": round(last_div, 4),
                "Total Stock Splits": total_splits,
            })
        else:
            summary.append({
                "Ticker": ticker,
                "Total Dividends ($)": 0,
                "Last Dividend ($)": 0,
                "Total Stock Splits": 0,})

    st.subheader("Summary")
    st.dataframe(pd.DataFrame(summary), use_container_width=True)

    st.markdown("---")
    selected = st.selectbox("Select Ticker for Detail", tickers)
    actions_df = corporate_actions[selected]

    if not actions_df.empty and "Dividends" in actions_df.columns:
        divs = actions_df[actions_df["Dividends"] > 0]
        if not divs.empty:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.bar(divs.index, divs["Dividends"], color="#2ca02c", width=20)
            ax.set_xlabel("Date")
            ax.set_ylabel("Dividend ($)")
            ax.set_title(f"{selected} Dividend History")
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
            plt.xticks(rotation=30)
            st.pyplot(fig)
        st.dataframe(actions_df[actions_df.select_dtypes(include="number").sum(axis=1) > 0], use_container_width=True)
    else:
        st.info(f"No corporate actions data available for {selected}.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — RAW DATA
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Raw Data":
    st.title("🗄️ Raw Data Explorer")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        selected_ticker = st.selectbox("Select Ticker", tickers)
    with col2:
        show_anomalies = st.checkbox("Show anomalies only", value=False)

    df = data[selected_ticker].copy()
    df["Daily_Return_%"] = (df["Daily_Return"] * 100).round(4)
    df["Anomaly"] = abs(df["Daily_Return"]) > 0.10
    df = df.drop(columns=["Daily_Return"])

    if show_anomalies:
        df = df[df["Anomaly"] == True]
        st.warning(f"{len(df)} anomalous records for {selected_ticker}")
    else:
        st.info(f"{len(df)} records for {selected_ticker}")

    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("Descriptive Statistics")
    st.dataframe(
        data[selected_ticker][["Close", "Volume", "Daily_Return"]].describe().round(4),
        use_container_width=True
    )

    csv = df.to_csv().encode("utf-8")
    st.download_button(
        label=f"Download {selected_ticker} data as CSV",
        data=csv,
        file_name=f"{selected_ticker}_data.csv",
        mime="text/csv"
    )