#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python3"
fi

"$PYTHON" -m src.run_pipeline --root .
"$PYTHON" -m src.export_paper_assets --root .
"$PYTHON" -m pytest

echo
echo "Final reproducibility overview"
"$PYTHON" - <<'PY'
import pandas as pd

overview = pd.read_csv("data/processed/reproducibility_overview.csv")
for _, row in overview.iterrows():
    print(f"- {row['category']}: {int(row['count'])}")
print("- package_type: reconstructed validation package, not full raw reproduction")
true_mismatch = int(overview.loc[overview["category"] == "TRUE_MISMATCH", "count"].iloc[0])
print(f"- critical_contradictions: {'none' if true_mismatch == 0 else true_mismatch}")
PY
