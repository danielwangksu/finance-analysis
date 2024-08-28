import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import argparse

# Actually I need rolling 20 years starting from every month given the input https://www.schwab.com/learn/story/does-market-timing-work


def fetch_stock_data(symbol, start_date, end_date):
    """Fetch stock data for the given symbol and date range."""
    stock = yf.Ticker(symbol)
    data = stock.history(start=start_date, end=end_date)
    return data


def calculate_strategy_returns(data, annual_investment, strategy_func):
    """Calculate returns for a given strategy."""
    if data.empty:
        print(f"Warning: No data available for the specified date range.")
        return 0, []
    return strategy_func(data, annual_investment)


def perfect_market_timing(data, annual_investment):
    """Simulate perfect market timing strategy. Buy at the lowest point of the year"""
    yearly_lows = data.resample("YE")["Low"].min()

    portfolio_value = 0
    shares_owned = 0
    buying_points = []

    for year, low_price in yearly_lows.items():
        if pd.isna(low_price):
            continue  # Skip years with no data

        shares_bought = annual_investment / low_price
        shares_owned += shares_bought
        buying_points.append((year, low_price))

    # After the loop, calculate the portfolio value using the last available closing price
    last_close = data["Close"].iloc[-1]  # Get the last closing price in the dataset
    portfolio_value = shares_owned * last_close

    return portfolio_value, buying_points


def immediate_investing(data, annual_investment):
    """Simulate immediate investing strategy."""
    yearly_first_days = data.resample("YS")["Open"].first()

    portfolio_value = 0
    shares_owned = 0
    buying_points = []

    for year, first_day_price in yearly_first_days.items():
        if pd.isna(first_day_price):
            continue  # Skip years with no data

        shares_bought = annual_investment / first_day_price
        shares_owned += shares_bought
        buying_points.append((year, first_day_price))

    # Calculate the portfolio value using the last available closing price
    last_close = data["Close"].iloc[-1]  # Get the last closing price in the dataset
    portfolio_value = shares_owned * last_close

    return portfolio_value, buying_points


def calculate_returns(final_value, total_invested, years):
    """Calculate total return and average annual return rate."""
    if total_invested == 0 or years == 0:
        # Return 0% for both total and annual return if no investment was made or time period is 0
        return (0, 0)

    total_return = (final_value - total_invested) / total_invested * 100

    if final_value <= 0:
        # If final value is 0 or negative, consider it a 100% loss
        avg_annual_return = -100
    else:
        avg_annual_return = (
            np.power((final_value / total_invested), (1 / years)) - 1
        ) * 100

    return total_return, avg_annual_return


def visualize_strategies_interactive(
    data, strategies_results, start_date, end_date, symbol
):
    """Create an interactive visualization of multiple investment strategies."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add stock data
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Close"],
            name=f"{symbol} Price",
            line=dict(color="gray", width=1),
        ),
        secondary_y=False,
    )

    colors = ["green", "red", "blue", "purple", "orange"]  # Add more colors if needed

    for (strategy_name, (_, buying_points)), color in zip(
        strategies_results.items(), colors
    ):
        x = [point[0] for point in buying_points]
        y = [point[1] for point in buying_points]
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                name=f"{strategy_name} Buy Points",
                marker=dict(color=color, size=8),
            ),
            secondary_y=False,
        )

    # Update layout
    fig.update_layout(
        title=f"{symbol} and Investment Strategies Buying Points<br>{start_date} to {end_date}",
        xaxis_title="Date",
        yaxis_title=f"{symbol} Price",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # Update y-axes
    fig.update_yaxes(title_text=f"{symbol} Price", secondary_y=False)

    # Save as interactive HTML
    fig.write_html("interactive_investment_strategies.html")
    print("Interactive visualization saved as 'interactive_investment_strategies.html'")


# def calculate_rolling_returns(data, annual_investment, window_years=20):
#     """Calculate returns for rolling periods."""
#     perfect_timing_returns = []
#     immediate_investing_returns = []
#     start_dates = []

#     for start_date in data.index[: -window_years * 365]:
#         end_date = start_date + pd.DateOffset(years=window_years)
#         period_data = data.loc[start_date:end_date]

#         perfect_timing_value = perfect_market_timing(period_data, annual_investment)
#         immediate_investing_value = immediate_investing(period_data, annual_investment)

#         total_invested = annual_investment * window_years

#         perfect_return, perfect_annual = calculate_returns(
#             perfect_timing_value, total_invested, window_years
#         )
#         immediate_return, immediate_annual = calculate_returns(
#             immediate_investing_value, total_invested, window_years
#         )

#         perfect_timing_returns.append((perfect_return, perfect_annual))
#         immediate_investing_returns.append((immediate_return, immediate_annual))
#         start_dates.append(start_date)

#     return pd.DataFrame(
#         {
#             "Start Date": start_dates,
#             "Perfect Timing Total Return": [r[0] for r in perfect_timing_returns],
#             "Perfect Timing Annual Return": [r[1] for r in perfect_timing_returns],
#             "Immediate Investing Total Return": [
#                 r[0] for r in immediate_investing_returns
#             ],
#             "Immediate Investing Annual Return": [
#                 r[1] for r in immediate_investing_returns
#             ],
#         }
#     )


def parse_arguments():
    """Parse command line arguments with default values."""
    parser = argparse.ArgumentParser(description="Analyze investment strategies")
    parser.add_argument(
        "--symbol",
        type=str,
        default="SPY",
        help="Stock symbol to analyze (default: SPY)",
    )
    parser.add_argument(
        "--start_date",
        type=str,
        default="1993-01-29",
        help="Start date in YYYY-MM-DD format (default: 1993-01-29, (the first available data for SPY))",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=20,
        help="Number of years for investment period (default: 20)",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=0,
        help="Additional months for investment period (default: 0)",
    )
    parser.add_argument(
        "--annual_investment",
        type=float,
        default=2000,
        help="Annual investment amount (default: 2000)",
    )

    args = parser.parse_args()
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    # end_date = start_date + timedelta(days=365 * args.years + 30 * args.months)
    # this correctly adjusts leap years, and the varying number of days in different months.
    end_date = start_date + relativedelta(years=args.years, months=args.months)

    return (
        args.symbol,
        args.start_date,
        end_date.strftime("%Y-%m-%d"),
        args.annual_investment,
    )


def main():
    symbol, start_date, end_date, annual_investment = parse_arguments()

    print(f"Analyzing {symbol} from {start_date} to {end_date}")
    print(f"Annual investment: ${annual_investment:,.2f}")

    data = fetch_stock_data(symbol, start_date, end_date)

    if data.empty:
        print(f"Error: No data available for {symbol} in the specified date range.")
        return

    strategies = {
        "Perfect Market Timing": perfect_market_timing,
        "Immediate Investing": immediate_investing,
    }

    results = {}
    for strategy_name, strategy_func in strategies.items():
        final_value, buying_points = calculate_strategy_returns(
            data, annual_investment, strategy_func
        )
        total_invested = annual_investment * len(buying_points)
        years = max(
            (data.index[-1] - data.index[0]).days / 365.25, 1
        )  # Ensure at least 1 year
        total_return, avg_annual_return = calculate_returns(
            final_value, total_invested, years
        )

        results[strategy_name] = (final_value, buying_points)

        print(f"\n{strategy_name} Strategy:")
        print(f"Final portfolio value: ${final_value:,.2f}")
        print(f"Total return: {total_return:.2f}%")
        print(f"Average annual return rate: {avg_annual_return:.2f}%")

    if all(len(buying_points) == 0 for _, (_, buying_points) in results.items()):
        print(
            "Warning: No valid buying points found for any strategy. Check your date range and data availability."
        )
    else:
        visualize_strategies_interactive(data, results, start_date, end_date, symbol)
    # # rolling_returns = calculate_rolling_returns(data, annual_investment)

    # print("\nRolling 20-Year Returns Summary:")
    # print(rolling_returns.describe())

    # print("\nSaving detailed results to 'rolling_returns.csv'")
    # rolling_returns.to_csv("rolling_returns.csv", index=False)

    # # Visualize buying points
    # visualize_buying_points(data, annual_investment, start_date, end_date)

    # # Create interactive visualization
    # visualize_buying_points_interactive(data, annual_investment, start_date, end_date)


if __name__ == "__main__":
    main()
