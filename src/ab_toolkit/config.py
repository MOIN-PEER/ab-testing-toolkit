from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RESULTS = ROOT / "outputs" / "results"
FIGURES = ROOT / "outputs" / "figures"
REPORTS = ROOT / "outputs" / "reports"
SEED = 42
ALPHA = 0.05
POWER = 0.80
SRM_ALPHA = 0.001          # sample-ratio-mismatch check uses a strict threshold, as is common practice
