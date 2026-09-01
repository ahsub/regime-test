def backtest_daily(returns):
    print("\n🔧 Führe täglichen Backtest durch...")
    # Entferne NaN-Werte zu Beginn
    returns_clean = returns.dropna()
    if len(returns_clean) == 0:
        return {'sharpe_ratio': 0.0, 'total_return': 0.0, 'n_days': 0}
    
    positions = pd.Series(1.0, index=returns_clean.index)
    strategy_returns = positions.shift(1).fillna(0) * returns_clean
    excess_returns = strategy_returns - 0.02/252
    
    if np.std(excess_returns) > 0:
        sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns)
    else:
        sharpe = 0.0
    
    strategy_cum = (1 + strategy_returns).cumprod()
    
    # Sicherer Zugriff
    if len(strategy_cum) > 0:
        last_val = strategy_cum.iloc[-1]
        if isinstance(last_val, pd.Series):
            last_val = last_val.iloc[0]
        total_return = float(last_val - 1) if last_val is not None else 0.0
    else:
        total_return = 0.0
    
    return {
        'sharpe_ratio': float(sharpe),
        'total_return': total_return,
        'n_days': len(returns_clean)
    }
