import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc


def fetch_stock_data(symbol, start_date, end_date):
    """Fetch stock data for the given symbol and date range."""
    stock = yf.Ticker(symbol)
    data = stock.history(start=start_date, end=end_date)
    return data


def perfect_market_timing(data, annual_investment):
    """Simulate perfect market timing strategy."""
    yearly_lows = data.groupby(data.index.to_period("Y")).agg(
        {"Low": ["min", "idxmin"]}
    )
    yearly_lows.columns = ["Low", "Date"]

    shares_owned = 0
    buying_points = []

    for year, row in yearly_lows.iterrows():
        low_price = row["Low"]
        buy_date = row["Date"]

        if pd.isna(low_price) or pd.isna(buy_date):
            continue  # Skip years with no data

        shares_bought = annual_investment / low_price
        shares_owned += shares_bought
        buying_points.append((buy_date, low_price))

    # Calculate the portfolio value using the last available closing price
    last_close = data["Close"].iloc[-1]  # Get the last closing price in the dataset
    portfolio_value = shares_owned * last_close

    return portfolio_value, buying_points


def immediate_investing(data, annual_investment):
    """Simulate immediate investing strategy."""
    yearly_first_days = data.groupby(data.index.to_period("Y")).first()

    shares_owned = 0
    buying_points = []

    for year, row in yearly_first_days.iterrows():
        first_day_price = row["Open"]
        buy_date = row.name.to_timestamp()  # Convert period to timestamp

        if pd.isna(first_day_price) or pd.isna(buy_date):
            continue  # Skip years with no data

        shares_bought = annual_investment / first_day_price
        shares_owned += shares_bought
        buying_points.append((buy_date, first_day_price))

    # Calculate the portfolio value using the last available closing price
    last_close = data["Close"].iloc[-1]  # Get the last closing price in the dataset
    portfolio_value = shares_owned * last_close

    return portfolio_value, buying_points


def dollar_cost_averaging(data, annual_investment):
    """Simulate dollar-cost averaging strategy."""
    monthly_investment = annual_investment / 12
    monthly_first_days = data.resample("MS").first()

    shares_owned = 0
    buying_points = []

    for date, row in monthly_first_days.iterrows():
        first_day_price = row["Open"]

        if pd.isna(first_day_price):
            continue  # Skip months with no data

        shares_bought = monthly_investment / first_day_price
        shares_owned += shares_bought
        buying_points.append((date, first_day_price))

    # Calculate the portfolio value using the last available closing price
    last_close = data["Close"].iloc[-1]  # Get the last closing price in the dataset
    portfolio_value = shares_owned * last_close

    return portfolio_value, buying_points


def invest_at_peaks(data, annual_investment):
    """Simulate investing at market peaks strategy."""
    yearly_peaks = data.groupby(data.index.to_period("Y")).agg(
        {"High": ["max", "idxmax"]}
    )
    yearly_peaks.columns = ["High", "Date"]

    shares_owned = 0
    buying_points = []

    for year, row in yearly_peaks.iterrows():
        peak_price = row["High"]
        invest_date = row["Date"]

        if pd.isna(peak_price) or pd.isna(invest_date):
            continue  # Skip years with no data

        shares_bought = annual_investment / peak_price
        shares_owned += shares_bought
        buying_points.append((invest_date, peak_price))

    # Calculate the portfolio value using the last available closing price
    last_close = data["Close"].iloc[-1]  # Get the last closing price in the dataset
    portfolio_value = shares_owned * last_close

    return portfolio_value, buying_points


strategies = {
    "Perfect Market Timing": perfect_market_timing,
    "Immediate Investing": immediate_investing,
    "Dollar-cost Averaging": dollar_cost_averaging,
    "Invest at Peaks": invest_at_peaks,
}


def calculate_rolling_analysis(
    symbol, start_date, years, annual_investment, selected_strategies, windows_years=1
):
    """Perform rolling analysis, shifting the start date by one month."""
    rolling_results = []
    start_date = pd.to_datetime(start_date)
    # end_date = start_date + pd.DateOffset(years=windows_years) + pd.DateOffset(months=1)
    max_date = pd.to_datetime("today") - pd.DateOffset(years=years)

    while start_date <= max_date:
        data = fetch_stock_data(
            symbol, start_date, start_date + pd.DateOffset(years=years)
        )
        if data.empty:
            break

        for strategy_name in selected_strategies:
            strategy_func = strategies[strategy_name]
            final_value, _ = strategy_func(data, annual_investment)
            total_invested = annual_investment * years
            total_return, avg_annual_return = calculate_returns(
                final_value, total_invested, years
            )

            rolling_results.append(
                {
                    "Strategy": strategy_name,
                    "Start Date": start_date.date(),
                    "End Date": (start_date + pd.DateOffset(years=years)).date(),
                    "Total Return (%)": total_return,
                    "Avg Annual Return (%)": avg_annual_return,
                }
            )

        start_date += pd.DateOffset(months=1)

    return rolling_results


def format_rolling_analysis_table(rolling_results):
    """Format rolling analysis results into a table."""
    table_header = html.Thead(
        html.Tr(
            [
                html.Th("Strategy"),
                html.Th("Start Date"),
                html.Th("End Date"),
                html.Th("Total Return (%)"),
                html.Th("Avg Annual Return (%)"),
            ]
        )
    )

    table_rows = []
    for index, result in enumerate(rolling_results):
        row_style = {"borderTop": "2px solid black" if index % 4 == 0 else "none"}
        table_rows.append(
            html.Tr(
                [
                    html.Td(result["Strategy"]),
                    html.Td(result["Start Date"]),
                    html.Td(result["End Date"]),
                    html.Td(f"{result['Total Return (%)']:.2f}"),
                    html.Td(f"{result['Avg Annual Return (%)']:.2f}"),
                ],
                style=row_style,
            )
        )

    table_body = html.Tbody(table_rows)

    table = dbc.Table(
        children=[table_header, table_body],
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
        className="table table-striped table-bordered",  # Add Bootstrap classes for additional styling
    )
    return table


def calculate_returns(final_value, total_invested, years):
    """Calculate total return and average annual return rate."""
    if total_invested == 0 or years == 0:
        return 0, 0

    total_return = (final_value - total_invested) / total_invested * 100

    if final_value <= 0:
        avg_annual_return = -100
    else:
        avg_annual_return = (
            np.power((final_value / total_invested), (1 / years)) - 1
        ) * 100

    return total_return, avg_annual_return


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div(
    [
        html.H1("Investment Strategy Analyzer"),
        html.Div(
            [
                html.Label("Stock Symbol:"),
                dcc.Input(id="symbol-input", value="SPY", type="text"),
                html.Label("Start Date:"),
                dcc.DatePickerSingle(
                    id="start-date-picker", date=datetime(1993, 1, 29)
                ),
                html.Label("Investment Period (Years):"),
                dcc.Input(id="years-input", value=20, type="number"),
                html.Label("Annual Investment ($):"),
                dcc.Input(id="investment-input", value=2000, type="number"),
                html.Label("Select Strategies:"),
                dcc.Checklist(
                    id="strategy-checklist",
                    options=[
                        {
                            "label": "Perfect Market Timing",
                            "value": "Perfect Market Timing",
                        },
                        {
                            "label": "Immediate Investing",
                            "value": "Immediate Investing",
                        },
                        {
                            "label": "Dollar-cost Averaging",
                            "value": "Dollar-cost Averaging",
                        },
                        {
                            "label": "Invest at Peaks",
                            "value": "Invest at Peaks",
                        },
                    ],
                    value=[
                        "Perfect Market Timing",
                        "Immediate Investing",
                        "Dollar-cost Averaging",
                        "Invest at Peaks",
                    ],
                    inline=True,
                ),
                html.Button("Analyze", id="analyze-button", n_clicks=0),
                html.Button("Rolling Analysis", id="rolling-button", n_clicks=0),
            ]
        ),
        html.Div(id="results-container"),
        dcc.Graph(id="strategy-graph", style={"height": "100vh", "width": "100%"}),
        html.Div(id="rolling-results-container"),
    ],
    style={
        "height": "100vh",
        "width": "100vw",
    },  # This ensures the entire layout fills the viewport
)


@app.callback(
    [Output("results-container", "children"), Output("strategy-graph", "figure")],
    [Input("analyze-button", "n_clicks")],
    [
        State("symbol-input", "value"),
        State("start-date-picker", "date"),
        State("years-input", "value"),
        State("investment-input", "value"),
        State("strategy-checklist", "value"),
    ],
)
def update_results(
    analyze_clicks,
    symbol,
    start_date,
    years,
    annual_investment,
    selected_strategies,
):
    if analyze_clicks is None or analyze_clicks == 0:
        return "", go.Figure()  # Return empty results if no button click

    start_date = pd.to_datetime(start_date)

    end_date = start_date + pd.DateOffset(years=years)

    data = fetch_stock_data(symbol, start_date, end_date)

    if data.empty:
        return (
            f"Error: No data available for {symbol} in the specified date range.",
            go.Figure(),
        )

    results = {}
    results_output = []
    for strategy_name in selected_strategies:
        strategy_func = strategies[strategy_name]
        final_value, buying_points = strategy_func(data, annual_investment)
        total_invested = annual_investment * years
        # years_invested = max((data.index[-1] - data.index[0]).days / 365.25, 1)
        total_return, avg_annual_return = calculate_returns(
            final_value, total_invested, years
        )

        results[strategy_name] = (final_value, buying_points)

        results_output.extend(
            [
                html.H3(f"{strategy_name} Strategy:"),
                html.P(f"Final portfolio value: ${final_value:,.2f}"),
                html.P(f"Total invested: ${total_invested:,.2f}"),
                html.P(f"Total return: {total_return:.2f}%"),
                html.P(f"Average annual return rate: {avg_annual_return:.2f}%"),
            ]
        )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Close"],
            name=f"{symbol} Price",
            line=dict(color="gray", width=1),
        )
    )

    colors = ["green", "red", "blue", "purple", "orange"]
    for (strategy_name, (_, buying_points)), color in zip(results.items(), colors):
        x = [point[0] for point in buying_points]
        y = [point[1] for point in buying_points]
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                name=f"{strategy_name} Buy Points",
                marker=dict(color=color, size=8),
            )
        )

    # Add dotted lines between years
    year_markers = pd.date_range(start=start_date, end=end_date, freq="YS")
    for marker in year_markers:
        fig.add_vline(x=marker, line=dict(color="black", width=1, dash="dot"))

    fig.update_layout(
        title=f"{symbol} and Investment Strategies Buying Points<br>{start_date.date()} to {end_date.date()}",
        xaxis_title="Date",
        yaxis_title=f"{symbol} Price",
        hovermode="x unified",
        autosize=True,
    )

    return html.Div(results_output), fig


# Callback for Rolling Analysis Button
@app.callback(
    [Output("rolling-results-container", "children")],
    [Input("rolling-button", "n_clicks")],
    [
        State("symbol-input", "value"),
        State("start-date-picker", "date"),
        State("years-input", "value"),
        State("investment-input", "value"),
        State("strategy-checklist", "value"),
    ],
)
def update_rolling_analysis(
    rolling_clicks, symbol, start_date, years, annual_investment, selected_strategies
):
    if rolling_clicks is None or rolling_clicks == 0:
        return [""]  # Return empty results if no button click

    start_date = pd.to_datetime(start_date)

    data = fetch_stock_data(symbol, start_date, pd.to_datetime("today"))

    if data.empty:
        return [f"Error: No data available for {symbol}."]

    rolling_results = calculate_rolling_analysis(
        symbol, start_date, years, annual_investment, selected_strategies
    )
    rolling_results_output = format_rolling_analysis_table(rolling_results)

    return [rolling_results_output]


if __name__ == "__main__":
    app.run_server(debug=True)
