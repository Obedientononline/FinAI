"""Tax impact calculator for portfolio rebalancing.

Computes estimated tax liability for each proposed trade based on:
- Cost basis vs current price (unrealized gain/loss)
- Holding period (short-term vs long-term capital gains)
- Client's tax bracket
- Tax-loss harvesting opportunities
"""
from datetime import datetime, date
from typing import Dict, List, Any, Optional

def compute_tax_impact(position: Any, trade_action: str, shares_to_trade: float, 
                       current_price: float, tax_bracket: Dict[str, float]) -> Dict[str, Any]:
    """
    Returns:
    {
        'realized_gain_loss': float,
        'is_short_term': bool,
        'tax_rate': float,
        'estimated_tax': float,
        'holding_period_days': int,
        'tax_type': 'short_term' | 'long_term'
    }
    """
    if trade_action.lower() != 'sell' or shares_to_trade <= 0:
        return {
            'realized_gain_loss': 0.0,
            'is_short_term': False,
            'tax_rate': 0.0,
            'estimated_tax': 0.0,
            'holding_period_days': 0,
            'tax_type': 'none'
        }
        
    cost_basis_per_share = getattr(position, 'cost_basis_per_share', getattr(position, 'cost_basis', current_price))
    holding_period_days = getattr(position, 'holding_period_days', None)
    
    if holding_period_days is None:
        purchase_date_val = getattr(position, 'purchase_date', date.today())
        if isinstance(purchase_date_val, str):
            purchase_date = datetime.strptime(purchase_date_val, '%Y-%m-%d').date()
        elif isinstance(purchase_date_val, datetime):
            purchase_date = purchase_date_val.date()
        else:
            purchase_date = purchase_date_val
        holding_period_days = (date.today() - purchase_date).days
        
    is_short_term = holding_period_days <= 365
    
    realized_gain_loss_per_share = current_price - cost_basis_per_share
    total_realized_gain_loss = realized_gain_loss_per_share * shares_to_trade
    
    if is_short_term:
        tax_rate = tax_bracket.get('short_term_rate', 0.35)
        tax_type = 'short_term'
    else:
        tax_rate = tax_bracket.get('long_term_rate', 0.15)
        tax_type = 'long_term'
        
    # Only tax gains, losses have negative tax impact (savings)
    estimated_tax = total_realized_gain_loss * tax_rate
    
    return {
        'realized_gain_loss': total_realized_gain_loss,
        'is_short_term': is_short_term,
        'tax_rate': tax_rate,
        'estimated_tax': estimated_tax,
        'holding_period_days': holding_period_days,
        'tax_type': tax_type
    }

def identify_tlh_opportunities(positions: List[Any], current_prices: Dict[str, float], 
                               wash_sale_days: int = 30) -> List[Dict[str, Any]]:
    """
    Identify tax-loss harvesting opportunities.
    Returns list of positions with unrealized losses that:
    1. Have unrealized loss > $100 (material)
    2. Are not within wash-sale window (30 days from last purchase)
    3. Include suggested replacement ETF
    """
    REPLACEMENT_MAP = {
        'SPY': 'IVV', 'IVV': 'VOO', 'VOO': 'SPY',
        'AGG': 'BND', 'BND': 'AGG',
        'GLD': 'IAU', 'IAU': 'GLD',
        'VWO': 'EEM', 'EEM': 'VWO',
    }
    
    opportunities = []
    
    for pos in positions:
        symbol = getattr(pos, 'symbol', '')
        if symbol not in current_prices:
            continue
            
        current_price = current_prices[symbol]
        cost_basis = getattr(pos, 'cost_basis', current_price)
        shares = getattr(pos, 'shares', 0.0)
        
        unrealized_loss = (cost_basis - current_price) * shares
        
        if unrealized_loss > 100:
            purchase_date_val = getattr(pos, 'purchase_date', date.today())
            if isinstance(purchase_date_val, str):
                purchase_date = datetime.strptime(purchase_date_val, '%Y-%m-%d').date()
            elif isinstance(purchase_date_val, datetime):
                purchase_date = purchase_date_val.date()
            else:
                purchase_date = purchase_date_val
                
            days_since_purchase = (date.today() - purchase_date).days
            
            if days_since_purchase > wash_sale_days:
                opportunities.append({
                    'symbol': symbol,
                    'unrealized_loss': unrealized_loss,
                    'shares_to_sell': shares,
                    'replacement_symbol': REPLACEMENT_MAP.get(symbol, 'CASH'),
                    'days_since_purchase': days_since_purchase
                })
                
    return opportunities

def compute_portfolio_tax_summary(trades: List[Any], positions: List[Any], tax_bracket: Dict[str, float]) -> Dict[str, float]:
    """
    Aggregate tax impact across all trades.
    Returns:
    {
        'total_short_term_gains': float,
        'total_long_term_gains': float,
        'total_short_term_losses': float,
        'total_long_term_losses': float,
        'net_tax_impact': float,
        'tlh_savings': float,
        'effective_tax_rate': float
    }
    """
    total_st_gains = 0.0
    total_lt_gains = 0.0
    total_st_losses = 0.0
    total_lt_losses = 0.0
    net_tax_impact = 0.0
    tlh_savings = 0.0
    
    # Map positions for easy lookup
    pos_map = {getattr(p, 'symbol', ''): p for p in positions}
    
    for trade in trades:
        action = getattr(trade, 'action', 'BUY')
        symbol = getattr(trade, 'symbol', '')
        shares = getattr(trade, 'shares', 0.0)
        price = getattr(trade, 'price', 0.0)
        
        if action.upper() == 'SELL' and symbol in pos_map:
            impact = compute_tax_impact(pos_map[symbol], 'sell', shares, price, tax_bracket)
            gl = impact['realized_gain_loss']
            tax = impact['estimated_tax']
            
            if impact['is_short_term']:
                if gl > 0:
                    total_st_gains += gl
                else:
                    total_st_losses += abs(gl)
                    tlh_savings += abs(tax)
            else:
                if gl > 0:
                    total_lt_gains += gl
                else:
                    total_lt_losses += abs(gl)
                    tlh_savings += abs(tax)
                    
            net_tax_impact += tax
            
    total_gains = total_st_gains + total_lt_gains
    effective_tax_rate = 0.0 if total_gains == 0 else max(0.0, net_tax_impact / total_gains)
    
    return {
        'total_short_term_gains': total_st_gains,
        'total_long_term_gains': total_lt_gains,
        'total_short_term_losses': total_st_losses,
        'total_long_term_losses': total_lt_losses,
        'net_tax_impact': net_tax_impact,
        'tlh_savings': tlh_savings,
        'effective_tax_rate': effective_tax_rate
    }
