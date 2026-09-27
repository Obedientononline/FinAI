"""Market data provider with yfinance live data and mock fallback."""
import json
import os
from typing import List, Dict

def get_current_prices(symbols: List[str], use_mock: bool = False) -> Dict[str, float]:
    """Fetch current market prices. Falls back to mock data if live fails."""
    if use_mock:
        return _load_mock_prices(symbols)
    try:
        return _fetch_live_prices(symbols)
    except Exception:
        return _load_mock_prices(symbols)

def _fetch_live_prices(symbols: List[str]) -> Dict[str, float]:
    """Use yfinance to get real-time prices."""
    import yfinance as yf
    
    prices = {}
    fetch_symbols = []
    
    for sym in symbols:
        if sym.upper() == 'CASH':
            prices['CASH'] = 1.0
        else:
            fetch_symbols.append(sym)
            
    if not fetch_symbols:
        return prices
        
    tickers = yf.Tickers(' '.join(fetch_symbols))
    for sym in fetch_symbols:
        ticker = tickers.tickers[sym]
        # Use fast info or history to get the last price
        hist = ticker.history(period="1d")
        if not hist.empty:
            prices[sym] = float(hist['Close'].iloc[-1])
        else:
            raise ValueError(f"Could not fetch price for {sym}")
            
    return prices
    
def _load_mock_prices(symbols: List[str]) -> Dict[str, float]:
    """Load from data/market_data.json"""
    # Assuming there's a data dir at the project root
    mock_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'market_data.json')
    prices = {}
    
    if os.path.exists(mock_file):
        with open(mock_file, 'r', encoding='utf-8') as f:
            mock_data = json.load(f)
    else:
        # Hardcoded fallback if file is missing
        mock_data = {
            'SPY': 500.0,
            'IVV': 505.0,
            'VOO': 460.0,
            'AGG': 97.0,
            'BND': 72.0,
            'GLD': 215.0,
            'IAU': 40.0,
            'VWO': 42.0,
            'EEM': 40.0,
            'CASH': 1.0
        }
        
    for sym in symbols:
        prices[sym] = float(mock_data.get(sym, 100.0))  # default 100.0 if not found
        if sym.upper() == 'CASH':
            prices[sym] = 1.0
            
    return prices
