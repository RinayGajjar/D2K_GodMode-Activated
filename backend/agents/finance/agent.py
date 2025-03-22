# Add this at the very top of the file, before any imports
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend - MUST BE BEFORE plt import

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from pathlib import Path
from datetime import datetime, timedelta
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FinanceAnalyzer")


class FinanceAnalyzer:
    """Finance agent for analyzing stock data"""

    def __init__(self):
        self.supported_files = ["csv", "txt"]
        # Configure matplotlib for non-interactive use
        plt.ioff()  # Turn interactive mode off

    def process_tickers(self, tickers_list):
        """Process a list of stock tickers directly with better error handling"""
        # Ensure tickers are valid strings and capitalized
        tickers = []
        for ticker in tickers_list:
            if ticker:
                try:
                    tickers.append(str(ticker).strip().upper())
                except Exception as e:
                    logger.error(f"Error processing ticker {ticker}: {str(e)}")

        # Limit to first 5 tickers for performance
        tickers = tickers[:5]

        if not tickers:
            return {"results": [], "charts": [], "message": "No valid tickers provided"}

        return self._analyze_tickers(tickers)

    def process_file(self, file_path, file_type):
        """Process a file with stock tickers"""
        try:
            if Path(file_path).suffix[1:].lower() == "csv":
                # Read CSV file with tickers
                df = pd.read_csv(file_path)
                if "ticker" in df.columns:
                    tickers = df["ticker"].tolist()
                else:
                    # Use first column
                    tickers = df.iloc[:, 0].tolist()
            else:
                # Read text file with tickers
                with open(file_path, "r") as f:
                    tickers = [line.strip() for line in f if line.strip()]

            # Make sure tickers are strings
            valid_tickers = []
            for ticker in tickers:
                if ticker is not None:
                    try:
                        valid_tickers.append(str(ticker).strip().upper())
                    except Exception as e:
                        logger.error(f"Error processing ticker {ticker}: {str(e)}")

            # Limit to first 5 tickers for performance
            valid_tickers = valid_tickers[:5]

            if not valid_tickers:
                return {
                    "results": [],
                    "charts": [],
                    "message": "No valid tickers found in file",
                }

            return self._analyze_tickers(valid_tickers)

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            return {"error": str(e), "results": [], "charts": []}

    def _analyze_tickers(self, tickers):
        """Analyze a list of ticker symbols with better error handling"""
        # Get stock data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 year of data

        results = []
        charts = []

        for ticker in tickers:
            try:
                logger.info(f"Processing ticker: {ticker}")

                # Get stock data with retry logic
                retry_count = 0
                max_retries = 3
                stock = None

                while retry_count < max_retries:
                    try:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(start=start_date, end=end_date)

                        if not hist.empty:
                            break

                        logger.warning(f"Empty history for {ticker}, retrying...")
                        retry_count += 1
                        time.sleep(1)  # Wait before retry
                    except Exception as inner_e:
                        logger.warning(
                            f"Retry {retry_count} failed for {ticker}: {str(inner_e)}"
                        )
                        retry_count += 1
                        time.sleep(1)  # Wait before retry

                if stock is None or hist.empty:
                    results.append(
                        {"ticker": ticker, "status": "No data available after retries"}
                    )
                    continue

                # Calculate metrics
                returns = hist["Close"].pct_change().dropna()

                if len(returns) < 5:  # Not enough data points
                    results.append(
                        {"ticker": ticker, "status": "Insufficient price history"}
                    )
                    continue

                annualized_return = (
                    returns.mean() * 252 * 100
                )  # Annualized return in percentage
                volatility = (
                    returns.std() * (252**0.5) * 100
                )  # Annualized volatility in percentage
                sharpe = annualized_return / volatility if volatility > 0 else 0

                # Get company info with defaults for missing data
                info = stock.info if hasattr(stock, "info") else {}
                company_name = info.get("shortName", ticker)
                industry = info.get("industry", "N/A")
                sector = info.get("sector", "N/A")
                market_cap = info.get("marketCap", 0)

                # Format market cap
                if market_cap > 0:
                    if market_cap >= 1_000_000_000_000:
                        market_cap_str = f"${market_cap / 1_000_000_000_000:.2f}T"
                    elif market_cap >= 1_000_000_000:
                        market_cap_str = f"${market_cap / 1_000_000_000:.2f}B"
                    elif market_cap >= 1_000_000:
                        market_cap_str = f"${market_cap / 1_000_000:.2f}M"
                    else:
                        market_cap_str = f"${market_cap:.2f}"
                else:
                    market_cap_str = "N/A"

                try:
                    # Generate chart
                    plt.figure(figsize=(10, 6))
                    plt.plot(hist.index, hist["Close"])
                    plt.title(f"{company_name} ({ticker}) - Stock Price")
                    plt.xlabel("Date")
                    plt.ylabel("Price (USD)")
                    plt.grid(True)

                    # Save chart to buffer
                    buffer = io.BytesIO()
                    plt.savefig(buffer, format="png")
                    buffer.seek(0)
                    chart_data = base64.b64encode(buffer.read()).decode("utf-8")
                    plt.close()

                    charts.append({"ticker": ticker, "chart": chart_data})
                except Exception as chart_e:
                    logger.error(f"Error generating chart for {ticker}: {str(chart_e)}")
                    # Continue without chart

                # Generate recommendation
                if sharpe > 1:
                    recommendation = "**STRONG BUY** - Excellent risk-adjusted returns"
                elif sharpe > 0.5:
                    recommendation = "**BUY** - Good risk-adjusted returns"
                elif sharpe > 0:
                    recommendation = (
                        "**HOLD** - Positive but modest risk-adjusted returns"
                    )
                else:
                    recommendation = "**SELL** - Poor risk-adjusted returns"

                # Create analysis
                analysis = f"# {company_name} ({ticker}) Analysis\n\n"
                analysis += f"**Sector:** {sector}\n"
                analysis += f"**Industry:** {industry}\n"
                analysis += f"**Market Cap:** {market_cap_str}\n\n"
                analysis += f"## Performance Metrics\n\n"
                analysis += f"**Current Price:** ${hist['Close'].iloc[-1]:.2f}\n"

                if not hist["High"].empty and not hist["Low"].empty:
                    analysis += f"**52-Week High:** ${hist['High'].max():.2f}\n"
                    analysis += f"**52-Week Low:** ${hist['Low'].min():.2f}\n"

                analysis += f"**Annual Return:** {annualized_return:.2f}%\n"
                analysis += f"**Annual Volatility:** {volatility:.2f}%\n"
                analysis += f"**Sharpe Ratio:** {sharpe:.2f}\n\n"
                analysis += f"## Recommendation\n\n{recommendation}\n\n"

                # Safe metrics dictionary
                metrics = {
                    "current_price": float(hist["Close"].iloc[-1]),
                    "annual_return": float(annualized_return),
                    "annual_volatility": float(volatility),
                    "sharpe_ratio": float(sharpe),
                }

                if not hist["High"].empty and not hist["Low"].empty:
                    metrics["high_52w"] = float(hist["High"].max())
                    metrics["low_52w"] = float(hist["Low"].min())

                # Add to results
                results.append(
                    {
                        "ticker": ticker,
                        "company_name": company_name,
                        "analysis": analysis,
                        "metrics": metrics,
                    }
                )

            except Exception as e:
                logger.error(f"Error analyzing ticker {ticker}: {str(e)}")
                results.append({"ticker": ticker, "status": f"Error: {str(e)}"})

        return {"results": results, "charts": charts}
