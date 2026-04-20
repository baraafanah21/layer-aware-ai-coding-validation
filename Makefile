PYTHON := $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

.PHONY: all pipeline assets test summary

all: pipeline assets test summary

pipeline:
	$(PYTHON) -m src.run_pipeline --root .

assets:
	$(PYTHON) -m src.export_paper_assets --root .

test:
	$(PYTHON) -m pytest

summary:
	@$(PYTHON) -c 'import pandas as pd; overview = pd.read_csv("data/processed/reproducibility_overview.csv"); print("Final reproducibility overview"); [print("- " + row["category"] + ": " + str(int(row["count"]))) for row in overview.to_dict("records")]; tm = int(overview.loc[overview["category"] == "TRUE_MISMATCH", "count"].iloc[0]); print("- package_type: reconstructed validation package, not full raw reproduction"); print("- critical_contradictions: " + ("none" if tm == 0 else str(tm)))'
