def calculate_metrics(historical_data):
    """Calculate key financial metrics from historical price data"""
    # Calculate returns
    returns = historical_data['Close'].pct_change().dropna()
    
    # Calculate metrics
    annual_return = returns.mean() * 252 * 100  # Annualized return in percentage
    annual_volatility = returns.std() * (252 ** 0.5) * 100  # Annualized volatility
    sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
    
    # Current price
    current_price = float(historical_data['Close'].iloc[-1])
    
    return {
        "current_price": current_price,
        "annual_return": float(annual_return),
        "annual_volatility": float(annual_volatility),
        "sharpe_ratio": float(sharpe_ratio),
        "high_52w": float(historical_data['High'].max()),
        "low_52w": float(historical_data['Low'].min())
    }

def format_market_cap(market_cap):
    """Format market cap into a readable string"""
    if market_cap > 0:
        if market_cap >= 1_000_000_000_000:
            return f"${market_cap / 1_000_000_000_000:.2f}T"
        elif market_cap >= 1_000_000_000:
            return f"${market_cap / 1_000_000_000:.2f}B"
        elif market_cap >= 1_000_000:
            return f"${market_cap / 1_000_000:.2f}M"
        else:
            return f"${market_cap:.2f}"
    else:
        return "N/A"

def generate_recommendation(sharpe_ratio):
    """Generate investment recommendation based on Sharpe ratio"""
    if sharpe_ratio > 1:
        return "**STRONG BUY** - Excellent risk-adjusted returns"
    elif sharpe_ratio > 0.5:
        return "**BUY** - Good risk-adjusted returns"
    elif sharpe_ratio > 0:
        return "**HOLD** - Positive but modest risk-adjusted returns"
    else:
        return "**SELL** - Poor risk-adjusted returns"