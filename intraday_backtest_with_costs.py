"""
intraday_backtest_with_costs.py – Intraday-Backtest mit Transaktionskosten
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def calculate_performance_with_costs(df, price_col="SPY", transaction_cost=0.001):
    """Berechnet Performance mit Transaktionskosten."""
    df = df.copy()
    df = df.dropna(subset=[price_col, "position"])
    
    if len(df) < 10:
        return {
            "total_return": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "trades": 0,
            "avg_position": 0,
            "n_days": len(df),
            "transaction_costs": 0,
            "cost_impact": 0
        }
    
    df["returns"] = df[price_col].pct_change()
    df["position_change"] = df["position"].diff().abs().fillna(0)
    df["strategy_returns"] = df["position"].shift(1) * df["returns"] - transaction_cost * df["position_change"]
    df["cumulative_returns"] = (1 + df["strategy_returns"]).cumprod()
    
    total_return = df["cumulative_returns"].iloc[-1] - 1
    
    if df["strategy_returns"].std() > 0:
        sharpe = df["strategy_returns"].mean() / df["strategy_returns"].std() * np.sqrt(252 * 6.5)
    else:
        sharpe = 0
    
    df["cummax"] = df["cumulative_returns"].cummax()
    df["drawdown"] = df["cumulative_returns"] / df["cummax"] - 1
    max_drawdown = df["drawdown"].min()
    
    trades = (df["position_change"] > 0.001).sum()
    total_costs = (transaction_cost * df["position_change"]).sum()
    cost_impact = total_costs / (abs(df["strategy_returns"]).sum() + 1e-10)
    
    return {
        "total_return": total_return,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_drawdown,
        "trades": trades,
        "avg_position": df["position"].mean(),
        "n_days": len(df),
        "transaction_costs": total_costs,
        "cost_impact": cost_impact
    }

def main():
    """Hauptfunktion."""
    print("=" * 60)
    print("📊 INTRADAY-BACKTEST MIT TRANSAKTIONSKOSTEN")
    print("=" * 60)
    
    data_path = Path(__file__).parent / "data" / "intraday" / "intraday_regimes.csv"
    
    if not data_path.exists():
        print(f"❌ Daten nicht gefunden: {data_path}")
        print("   Führen Sie zuerst intraday_regime.py aus")
        return
    
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    print(f"📊 Daten geladen: {len(df)} Zeilen")
    
    df_clean = df.dropna(subset=["position"])
    print(f"   Zeilen mit Position: {len(df_clean)}")
    
    # Teste verschiedene Kosten-Szenarien
    print("\n📈 PERFORMANCE-VERGLEICH:")
    print("   Kosten       Sharpe     Rendite      Trades")
    print("-" * 55)
    
    # Ohne Kosten
    from intraday_backtest import calculate_performance
    results_without = calculate_performance(df_clean, price_col="SPY")
    print(f"   0.00%        {results_without['sharpe_ratio']:<10.2f} "
          f"{results_without['total_return']*100:<11.2f}% "
          f"{results_without['trades']:<10}")
    
    # Mit Kosten
    for cost in [0.0005, 0.001, 0.002, 0.005]:
        results = calculate_performance_with_costs(df_clean, price_col="SPY", transaction_cost=cost)
        cost_pct = cost * 100
        print(f"   {cost_pct:.2f}%        {results['sharpe_ratio']:<10.2f} "
              f"{results['total_return']*100:<11.2f}% "
              f"{results['trades']:<10}")
    
    # Details mit 0.1%
    print("\n" + "=" * 60)
    print("📊 DETAILS (0.1% Transaktionskosten)")
    print("=" * 60)
    
    results = calculate_performance_with_costs(df_clean, price_col="SPY", transaction_cost=0.001)
    print(f"   Gesamtrendite:       {results['total_return']*100:.2f}%")
    print(f"   Sharpe Ratio:        {results['sharpe_ratio']:.2f}")
    print(f"   Max. Drawdown:       {results['max_drawdown']*100:.2f}%")
    print(f"   Anzahl Trades:       {results['trades']}")
    print(f"   Transaktionskosten:  {results['transaction_costs']*100:.4f}%")
    print(f"   Kosten-Einfluss:     {results['cost_impact']*100:.2f}%")
    
    results_path = Path(__file__).parent / "results" / "intraday_results_with_costs.csv"
    pd.DataFrame([results]).to_csv(results_path, index=False)
    print(f"\n💾 Ergebnisse gespeichert: {results_path}")

if __name__ == "__main__":
    main()
