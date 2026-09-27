import os
import sys
from dotenv import load_dotenv

# Ensure root and backend directories are in sys.path
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_BACKEND_DIR)
for p in [_ROOT_DIR, _BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

load_dotenv()

# API Keys
LYZR_API_KEY = os.getenv('LYZR_AGENT_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Model config
DEFAULT_MODEL = 'gpt-4o'
DEFAULT_PROVIDER = 'openai'

# Currency config (Indian Rupee INR)
CURRENCY_SYMBOL = "₹"
CURRENCY_CODE = "INR"

# Risk score boundaries
RISK_CATEGORIES = {
    'conservative': (1, 3),
    'moderate_conservative': (4, 4),
    'moderate': (5, 6),
    'moderate_aggressive': (7, 7),
    'aggressive': (8, 10),
}

# Default allocation ranges by risk category
DEFAULT_ALLOCATION_RANGES = {
    'conservative': {'equities': (0.10, 0.20), 'fixed_income': (0.50, 0.70), 'commodities': (0.0, 0.05), 'cash': (0.15, 0.30)},
    'moderate_conservative': {'equities': (0.20, 0.35), 'fixed_income': (0.40, 0.55), 'commodities': (0.0, 0.10), 'cash': (0.10, 0.20)},
    'moderate': {'equities': (0.35, 0.55), 'fixed_income': (0.25, 0.40), 'commodities': (0.05, 0.15), 'cash': (0.05, 0.15)},
    'moderate_aggressive': {'equities': (0.55, 0.70), 'fixed_income': (0.15, 0.30), 'commodities': (0.05, 0.15), 'cash': (0.05, 0.10)},
    'aggressive': {'equities': (0.70, 0.90), 'fixed_income': (0.05, 0.20), 'commodities': (0.05, 0.15), 'cash': (0.02, 0.10)},
}

# Tax rates
SHORT_TERM_HOLDING_DAYS = 365
LONG_TERM_CAP_GAINS_RATE = 0.15
SHORT_TERM_CAP_GAINS_RATES = {0.10: 0.10, 0.12: 0.12, 0.22: 0.22, 0.24: 0.24, 0.32: 0.32, 0.35: 0.35, 0.37: 0.37}

# Asset classification
ASSET_CLASS_MAP = {
    'SPY': 'equities', 'IVV': 'equities', 'VOO': 'equities', 'QQQ': 'equities',
    'AAPL': 'equities', 'MSFT': 'equities', 'GOOGL': 'equities', 'AMZN': 'equities',
    'VWO': 'equities', 'EFA': 'equities', 'VTI': 'equities',
    'AGG': 'fixed_income', 'BND': 'fixed_income', 'TLT': 'fixed_income',
    'LQD': 'fixed_income', 'HYG': 'fixed_income', 'TIPS': 'fixed_income',
    'GLD': 'commodities', 'SLV': 'commodities', 'DBC': 'commodities', 'USO': 'commodities',
    'CASH': 'cash', 'SHV': 'cash', 'BIL': 'cash',
}

# Portfolio constraints
DEFAULT_MAX_SINGLE_POSITION = 0.10
DEFAULT_REBALANCE_THRESHOLD = 0.05
MAX_TURNOVER_PER_REBALANCE = 0.25
MIN_DIVERSIFICATION_CLASSES = 4
MIN_DIVERSIFICATION_AUM = 500000
TAX_EFFICIENCY_THRESHOLD = 5000
WASH_SALE_DAYS = 30
