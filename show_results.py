import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path('data/results')

# Prüfen, ob die CSV existiert
csv_file = OUTPUT_DIR / 'optimization_results.csv'
if csv_file.exists():
    results_df = pd.read_csv(csv_file)
    best = results_df.iloc[0]
    
    print("🏆 Beste Parameter-Kombination")
    print("=" * 40)
    print(f"Sharpe Ratio:     {best['sharpe_ratio']:.2f}")
    print(f"Gesamtrendite:    {best['total_return']:.2%}")
    print(f"\n🔧 Parameter:")
    print(f"   BULL_QUIET:       {best['bull_quiet']:.2f}")
    print(f"   STRESS:           {best['stress']:.2f}")
    print(f"   BULL_FRAGILE:     {best['bull_fragile']:.2f}")
    print(f"   REVERSION:        {best['reversion']:.2f}")
    print(f"   Bestätigungstage: {int(best['confirmation_days'])}")
else:
    print("❌ CSV-Datei nicht gefunden.")
    print("💡 Bitte öffnen Sie die Grafik: data/results/optimization_results.png")
    print("   Die besten Parameter sind dort in der oberen rechten Ecke sichtbar.")
