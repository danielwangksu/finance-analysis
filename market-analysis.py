import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt


def visualize_buying_points(data, annual_investment, start_date, end_date):
    """Visualize the buying points for both strategies."""
    plt.figure(figsize=(15, 10))

    # Plot S&P 500 data
    plt.plot(data.index, data["Close"], label="S&P 500", color="gray", alpha=0.7)

    # Perfect Market Timing buying points
    yearly_lows = data.resample("YE")["Low"].min()
    plt.scatter(
        yearly_lows.index,
        yearly_lows,
        color="green",
        label="Perfect Timing Buy Points",
        zorder=5,
    )

    # Immediate Investing buying points
    yearly_first_days = data.resample("YS")["Open"].first()
    plt.scatter(
        yearly_first_days.index,
        yearly_first_days,
        color="red",
        label="Immediate Investing Buy Points",
        zorder=5,
    )

    plt.title(
        f"S&P 500 and Investment Strategies Buying Points\n{start_date} to {end_date}"
    )
    plt.xlabel("Date")
    plt.ylabel("S&P 500 Index Value")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Annotate some points with investment amounts
    for i, (date, price) in enumerate(yearly_lows.items()):
        if i % 5 == 0:  # Annotate every 5th point to avoid clutter
            plt.annotate(
                f"${annual_investment}",
                (date, price),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
            )

    plt.tight_layout()
    plt.savefig("investment_strategies_visualization.png")
    print("Visualization saved as 'investment_strategies_visualization.png'")


def fetch_sp500_data(start_date, end_date):
    """Fetch S&P 500 data for the given date range."""
    sp500 = yf.Ticker("^GSPC")
    data = sp500.history(start=start_date, end=end_date)
    return data


def perfect_market_timing(data, annual_investment):
    """Simulate perfect market timing strategy."""
    yearly_lows = data.resample("YE")["Low"].min()

    portfolio_value = 0
    shares_owned = 0

    for year, low_price in yearly_lows.items():
        if pd.isna(low_price):
            continue  # Skip years with no data

        shares_bought = annual_investment / low_price
        shares_owned += shares_bought

        # Get the last available closing price for this year
        year_end = year.strftime("%Y-%m-%d")
        future_data = data.loc[year_end:]
        if not future_data.empty:
            last_close = future_data.iloc[-1]["Close"]
            portfolio_value = shares_owned * last_close

    return portfolio_value


def immediate_investing(data, annual_investment):
    """Simulate immediate investing strategy."""
    yearly_first_days = data.resample("YS")["Open"].first()

    portfolio_value = 0
    shares_owned = 0

    for year, first_day_price in yearly_first_days.items():
        if pd.isna(first_day_price):
            continue  # Skip years with no data

        shares_bought = annual_investment / first_day_price
        shares_owned += shares_bought

        # Get the last available closing price for this year
        year_end = year.strftime("%Y-%m-%d")
        future_data = data.loc[year_end:]
        if not future_data.empty:
            last_close = future_data.iloc[-1]["Close"]
            portfolio_value = shares_owned * last_close

    return portfolio_value


def main():
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")
    annual_investment = float(input("Enter annual investment amount: "))

    data = fetch_sp500_data(start_date, end_date)

    # Ensure we're only processing full years
    full_years = pd.to_datetime(end_date).year - pd.to_datetime(start_date).year

    perfect_timing_value = perfect_market_timing(data, annual_investment)
    immediate_investing_value = immediate_investing(data, annual_investment)

    total_invested = annual_investment * full_years

    print(f"\nInvestment Results over {full_years} years:")
    print(f"Total invested: ${total_invested:,.2f}")

    print(f"\nPerfect Market Timing Strategy:")
    print(f"Final portfolio value: ${perfect_timing_value:,.2f}")
    total_return, avg_annual_return = calculate_returns(
        perfect_timing_value, total_invested, full_years
    )
    print(f"Total return: {total_return:.2f}%")
    print(f"Average annual return rate: {avg_annual_return:.2f}%")

    print(f"\nImmediate Investing Strategy:")
    print(f"Final portfolio value: ${immediate_investing_value:,.2f}")
    total_return, avg_annual_return = calculate_returns(
        immediate_investing_value, total_invested, full_years
    )
    print(f"Total return: {total_return:.2f}%")
    print(f"Average annual return rate: {avg_annual_return:.2f}%")


if __name__ == "__main__":
    main()
