def daily_backtest(returns):
    """Täglicher Backtest zum Vergleich."""
    print("\n🔧 Führe täglichen Backtest durch...")
    signals = pd.DataFrame(index=returns.index)
    signals['position'] = 1.0
    
    positions = signals['position'].shift(1).fillna(0)
    strategy_returns = positions * returns
    
    excess_returns = strategy_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    strategy_cum = (1 + strategy_returns).cumprod()
    
    # KORREKTUR: Sicherer Zugriff auf den letzten Wert
    last_val = strategy_cum.iloc[-1] if len(strategy_cum) > 0 else 1.0
    if isinstance(last_val, pd.Series):
        last_val = last_val.iloc[0]
    total_return = float(last_val - 1) if last_val is not None else 0.0
    
    return {
        'sharpe_ratio': float(sharpe),
        'total_return': total_return,
        'n_days': len(signals)
    }
