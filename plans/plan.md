# Git LFS + Shiny for Python — Implementation Plan

## Objective

Test Git LFS by generating a large CSV dataset, tracking it with LFS, and
building a Shiny for Python front end to explore the data interactively.

## Components

### 1. Dataset Generator (`generate_dataset.py`)

- Generates a synthetic dataset with **1 million+ rows** across multiple columns.
- Columns include a mix of numeric, categorical, datetime, and text data to
  simulate a realistic large dataset (e.g., e-commerce transactions).
- Output: `data/transactions.csv` (~200–300 MB).

### 2. Git LFS Configuration

- Track `data/*.csv` via `.gitattributes`.
- Ensures the large CSV is stored in LFS rather than the Git object store.

### 3. Shiny for Python App (`app.py`)

The front end provides:

| Feature | Details |
|---|---|
| **Summary statistics** | Row count, column types, memory usage |
| **Filterable data table** | Paginated view of the raw data |
| **Visualisation — Sales over time** | Aggregated line chart of daily revenue |
| **Visualisation — Category breakdown** | Bar chart of transaction counts by category |
| **Sidebar controls** | Date range filter, category multi-select, sample size slider |

### 4. Requirements (`requirements.txt`)

- `shiny`
- `pandas`
- `numpy`

## File Layout

```
git-lfs-test/
├── .gitattributes          # LFS tracking rules
├── .gitignore              # Python ignores (existing)
├── requirements.txt        # Python dependencies
├── plans/
│   └── plan.md             # This plan
├── generate_dataset.py     # Dataset creation script
├── app.py                  # Shiny for Python front end
└── data/
    └── transactions.csv    # Generated large file (LFS-tracked)
```

## Execution Steps

1. Write this plan to `plans/plan.md`.
2. Initialise Git LFS and add tracking rule for `data/*.csv`.
3. Create `generate_dataset.py` and run it to produce the dataset.
4. Create `app.py` (Shiny for Python).
5. Create `requirements.txt`.
6. Commit everything and push to the feature branch.
