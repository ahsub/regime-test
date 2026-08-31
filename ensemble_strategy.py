def load_data():
    """Lädt die Signale beider Modelle und die Renditen."""
    print("📊 Lade Signale der Modelle...")
    
    # 1. VIX-Signale laden
    vix_signals = pd.read_csv(OUTPUT_DIR / 'trading_signals.csv', index_col=0, parse_dates=True)
    # Auf einheitliches Format bringen: datetime64[us]
    vix_signals.index = pd.to_datetime(vix_signals.index).tz_localize(None).as_unit('us')
    print(f"   📊 VIX-Signale: {len(vix_signals)} Tage")
    
    # 2. HMM-Labels laden
    hmm_labels = pd.read_csv(OUTPUT_DIR / 'rolling_hmm_enhanced_labels.csv', index_col=0, parse_dates=True)
    hmm_labels.index = pd.to_datetime(hmm_labels.index).tz_localize(None).as_unit('us')
    print(f"   📊 HMM-Labels: {len(hmm_labels)} Tage")
    
    # 3. Renditen von Yahoo Finance laden
    import yfinance as yf
    sp500 = yf.download('^GSPC', start='2011-01-01', end='2026-08-28', progress=False)
    returns = sp500['Close'].pct_change()
    # Auf einheitliches Format bringen: datetime64[us]
    returns.index = pd.to_datetime(returns.index).tz_localize(None).as_unit('us')
    print(f"   ✅ S&P 500 von Yahoo Finance geladen: {len(returns)} Tage")
    
    # Gemeinsame Tage finden
    common_dates = vix_signals.index.intersection(hmm_labels.index).intersection(returns.index)
    vix_signals = vix_signals.loc[common_dates]
    hmm_labels = hmm_labels.loc[common_dates]
    returns = returns.loc[common_dates]
    
    print(f"   ✅ {len(common_dates)} gemeinsame Tage gefunden")
    return vix_signals, hmm_labels, returns
