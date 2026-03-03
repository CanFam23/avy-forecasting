# Avy Forecasting

Forecasting pipeline and web dashboard for avalanche danger in the Whitefish, Swan, and Glacier/Flathead forecast zones in northwest Montana.

## What this project does

This project combines:

1. HRRR weather data retrieval (via Herbie)
2. SNOWPACK simulations at FAC forecast points
3. A trained Random Forest model to predict daily danger levels by zone/elevation
4. FAC forecast scraping for comparison against observed danger
5. AI-generated forecast discussion and a React dashboard for visualization

Primary outputs include:

- Daily predicted danger by zone and elevation
- Historical predicted vs actual comparisons
- Performance metrics and confusion matrices
- AI-written forecast narrative for each zone

## Repository layout

```text
.
├── src/
│   ├── workflows/
│   │   ├── ForecastPipeline.py   # Weather fetch + simulation + model predictions
│   │   └── FullPipeline.py       # ForecastPipeline + FAC scrape + web JSON outputs
│   ├── herbie/                   # HRRR fetching logic
│   ├── sim/                      # SNOWPACK integration
│   ├── scraping/                 # FAC scraper (Playwright)
│   └── util/                     # Data conversion, modeling, plotting, geo helpers
├── web/avyAI/                    # React + TypeScript frontend
├── data/                         # Models, fetched weather, predictions, FAC archives
├── notebooks/                    # Model experiments and visualization notebooks
└── docs/                         # UI drafts
```

## Prerequisites

### System

- Python 3.11+
- Node.js 20+ and npm
- SNOWPACK installed locally

### Python packages

Install Python dependencies from `requirements.txt`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
```

### Node packages

Frontend dependencies are defined in `web/avyAI/package.json`.

## Environment variables

Create a `.env` file in the project root with:

```env
DEFAULT_SNO_PATH=/absolute/path/to/data/input/sno
GEMINI_API_KEY=your_api_key
```

Notes:

- `GEMINI_API_KEY` is required for `src/util/web.py` AI forecast generation.
- `DEFAULT_SNO_PATH` is kept for pipeline config compatibility.

## Path configuration status

Path values in the current codebase are transitional and not final. A centralized config file is planned.

Until that is in place, treat any paths in this README and in `src/` as defaults/examples for local development.

## Running the project

### 1. Run forecast pipeline (backend only)

From repository root:

```bash
python -m src.workflows.ForecastPipeline
```

This runs:

1. Missing weather fetch for the season (`data/fetched`)
2. Forecast weather fetch
3. Snowpack simulation for missing prediction days
4. Model inference and daily aggregation

Key outputs:

- `data/ops25_26/all_predictions.csv`
- `data/ops25_26/day_predictions.csv`

### 2. Run full operational pipeline (backend + web data refresh)

From repository root:

```bash
python -m src.workflows.FullPipeline
```

This additionally:

1. Updates FAC archives
2. Converts predictions/actuals to web JSON payloads
3. Generates AI forecast discussion
4. Recomputes performance artifacts

Key web outputs:

- `web/avyAI/public/data/ai_forecast.json`
- `web/avyAI/public/data/actual_forecast.json`
- `web/avyAI/public/data/weather.json`
- `web/avyAI/public/data/forecast_discussion.json`
- `web/avyAI/public/performance/performance_metrics.json`
- `web/avyAI/public/performance/cm.svg`
- `web/avyAI/public/performance/norm_cm.svg`
- `web/avyAI/public/performance/zone_ele_perf.svg`

### 3. Run the frontend dashboard

```bash
cd web/avyAI
npm install
npm run dev
```

Open the local Vite URL shown in the terminal (typically `http://localhost:5173`).

The app reads static JSON files in `web/avyAI/public/data` and `web/avyAI/public/performance`, so rerun the full pipeline to refresh dashboard content.

## Data flow summary

1. HRRR weather is fetched and split by point/season.
2. Weather is converted to SMET and passed to SNOWPACK.
3. SNOWPACK output is converted to CSV and daily features are aggregated.
4. Trained model (`data/models/best_model_4.pkl`) predicts danger at point/slope level.
5. Predictions are reduced to zone/elevation daily danger levels.
6. FAC observed danger is scraped and normalized for comparison.
7. JSON artifacts are produced for frontend plots and forecast cards.

## Known limitations

- Generalization varies by season; historical notebooks report stronger training fit than test performance.
- `src/sim/simulation.py` currently contains temporary hardcoded local absolute paths for SNOWPACK execution and `avyIO.ini`.
- Point `id == 202` is explicitly skipped during missing-prediction backfill in `ForecastPipeline`.
- Summer months (June through September) are intentionally excluded in missing-hour checks.

## Troubleshooting

- `playwright` browser errors: run `python -m playwright install chromium`.
- Missing Gemini forecast output: verify `.env` contains a valid `GEMINI_API_KEY`.
- SNOWPACK execution failures: confirm your local SNOWPACK binary path and `avyIO.ini` path match values currently used in `src/sim/simulation.py`.
- Empty frontend cards/plots: rerun `python -m src.workflows.FullPipeline` to regenerate JSON data.

## Data sources

- HRRR weather model (via Herbie)
- SNOWPACK physical snow model
- Flathead Avalanche Center (FAC) forecast archive and daily forecast pages

## Notes for contributors

- Keep generated artifacts in `web/avyAI/public` synchronized with pipeline outputs before demo/deploy.
- Model development and feature exploration live in `notebooks/model`.
