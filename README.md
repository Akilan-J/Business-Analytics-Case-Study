# Intelligent Food Delivery Analytics Using Live Swiggy Market Intelligence

**23CSE452 Business Analytics — Individual Case Study**

| | |
|---|---|
| **Student Name** | Akilan J |
| **Register Number** | CB.SC.U4CSE23002 |
| **Class / Section** | CSE-A |
| **Business Domain** | Food Delivery Analytics |
| **Data collected on** | 19 September 2026 |

---

## 1. Problem Statement

Food delivery aggregators list thousands of restaurants whose ratings, pricing,
promised delivery times and promotional offers vary sharply from one locality to
the next, yet neither the platform nor its restaurant partners have a clear view
of which of these attributes actually move customer-facing quality and delivery
performance. Because listings change continuously, analyses built on static
historical extracts describe a market that no longer exists. This study collects
**live restaurant-level listing data directly from Swiggy** across 70 localities in
7 Indian metros, and uses it to quantify the drivers of restaurant rating and
delivery time, to benchmark competing brands, and to segment restaurants by
price–quality–speed positioning so that pricing, discounting and operational
decisions can be grounded in current market evidence.

## 2. Objectives

1. Analyse the factors that influence food delivery performance.
2. Collect real-time restaurant information directly from Swiggy.
3. Compare competitor delivery times, pricing, ratings and promotional offers.
4. Build predictive models for delivery-time estimation and restaurant performance.
5. Generate business insights that improve operational efficiency and customer satisfaction.
6. Support strategic decision-making with live market data.

## 3. Data Collection

| | |
|---|---|
| **Source** | `https://www.swiggy.com/dapi/restaurants/list/v5` — the public JSON endpoint behind `swiggy.com/restaurants` |
| **Method** | Custom Python scraper (`scripts/scrape_swiggy.py`), one GET per locality centroid, randomised 1.2–2.4 s crawl delay |
| **Coverage** | 70 localities × 7 cities (Chennai, Bengaluru, Hyderabad, Mumbai, Delhi, Pune, Kolkata), 10 localities per city |
| **Records** | 1,831 restaurant × locality observations → **1,686 unique restaurants** |
| **Attributes** | 22 raw fields → 30 after feature engineering |
| **Authentication** | None. No login, no paid API, no personal data |

**Key variables:** average rating, rating count, cost for two, promised delivery
time, last-mile distance, cuisine tags, offer header/sub-header, chain parent id,
locality, city, availability.

No ready-made dataset (Kaggle / UCI / GitHub repositories) is used anywhere in
this study — the scraped data is the sole and primary dataset.

### Deviations from the approved proposal

| Proposed | Delivered | Reason |
|---|---|---|
| Historical Kaggle dataset + live data | Live scraped data only | Submission rules prohibit ready-made datasets as the primary source |
| Apify Swiggy Scraper | Purpose-built scraper on the same public endpoint | Same source and fields; no paid dependency; procedure fully auditable in this repo |
| Menu items and menu prices | Not collected | Swiggy's per-restaurant menu endpoint returns HTTP 202 to unauthenticated requests |
| Google ratings, weather, traffic | Not collected | Not exposed by any public Swiggy endpoint |

## 4. Analytics Methods

| Question | Method | Metric |
|---|---|---|
| What drives restaurant rating? | Multiple linear regression (OLS, HC3 robust SEs) + VIF, Breusch–Pagan, Q–Q diagnostics | Adjusted R² |
| Can a non-linear model do better? | Random Forest, Gradient Boosting + permutation importance | CV R², test R², RMSE, MAE |
| Which restaurants are highly rated? | Logistic regression (unweighted vs class-weighted) | ROC-AUC, precision/recall |
| How do restaurants position themselves? | K-Means (elbow + silhouette selection) | Silhouette score |
| What drives delivery time? | OLS + Random Forest + Gradient Boosting | Test R², MAE (minutes) |
| How do brands compare? | Brand-level roll-up and benchmark quadrant | Descriptive |
| Are offers linked to rating? | Chi-square test of independence, Welch's t-test | χ², p-value |

## 5. Key Results

| Metric | Value |
|---|---|
| Unique restaurants analysed | 1,686 |
| Restaurants carrying a rating | 99.8% |
| Median cost for two | ₹300 |
| Median promised delivery time | 27 min |
| Restaurants running a visible offer | 94.1% |
| Rating model — OLS adjusted R² | 0.260 |
| Rating model — Random Forest test R² | **0.487** |
| High-rating classifier — ROC-AUC | 0.726 |
| Delivery-time model — Gradient Boosting test R² | **0.651** (MAE 3.94 min) |
| Minutes added per extra km of last mile | **3.43** |
| K-Means segments (k = 4) — silhouette | 0.215 |

**Headline findings**

1. **Delivery time is highly predictable; rating is not.** Distance alone explains
   most of delivery time (test R² 0.651, MAE under 4 minutes), while the best
   rating model reaches only R² 0.487 — listing attributes do not capture food
   quality or service.
2. **Discounting is negatively associated with rating.** Restaurants running a
   discount of 50% or more average **4.23** vs **4.39** for everyone else
   (Welch t = −13.3, p < 0.001), and offer depth is the single strongest
   permutation-importance feature in the rating model.
3. **Price and rating move in opposite directions** (Spearman ρ = −0.24,
   p < 0.001). Budget restaurants average 4.41; premium ones 4.31.
4. **Each extra kilometre of last mile costs 3.43 minutes**, and the city effect
   is large — Pune is roughly 10 minutes faster than Kolkata at equal distance.
5. **Four positioning segments** emerge: Value performers (n=404, rating 4.55),
   Premium performers (n=442), Premium laggards (n=267, slowest at 35 min) and
   Value laggards (n=554, 63% average discount depth and the lowest rating).

## 6. Repository Contents

```
├── README.md                       this file
├── analysis.ipynb                  full executed analysis (36 code cells, 14 figures)
├── Case_Study_Report.pdf           final 6-page report in the prescribed format
├── data/
│   ├── swiggy_raw.csv              raw scrape, 1,831 rows
│   └── swiggy_clean.csv            cleaned + engineered, 1,686 rows
├── scripts/
│   ├── scrape_swiggy.py            the data collection scraper
│   ├── build_notebook.py           regenerates analysis.ipynb
│   └── build_report.py             regenerates Case_Study_Report.pdf
└── report/
    ├── figures/                    14 exported figures
    └── *.csv                       exported result tables
```

## 7. Reproducing

```bash
python3 scripts/scrape_swiggy.py                 # re-collect data/swiggy_raw.csv
python3 -m nbconvert --execute --to notebook --inplace analysis.ipynb
python3 scripts/build_report.py                  # rebuild the PDF
```

Listings change continuously, so a fresh scrape will not reproduce these numbers
exactly. `data/swiggy_raw.csv` is the frozen 19 September 2026 snapshot that this
report is built on.

## 8. Ethics and Compliance

- Only publicly displayed **business** attributes are collected — no customer
  names, reviews, addresses or personal identifiers.
- A randomised 1.2–2.4 s delay is applied between requests to avoid load on the
  source.
- Data is used solely for this academic case study.

## 9. References

1. Garg, A., Ayaan, M., Parekh, S. and Udandarao, V. (2025) *Food Delivery Time Prediction in Indian Cities Using Machine Learning Models.* arXiv:2503.15177. https://arxiv.org/abs/2503.15177
2. Turai, S., Praneetha, P., Aishwarya, R. B., Adil, M. and Vangala, M. C. (2025) 'Analysis of restaurant ratings and reviews using machine learning', *World Journal of Advanced Research and Reviews*, 25(02), pp. 1039–1046. https://doi.org/10.30574/wjarr.2025.25.2.0378
3. Raj, H., Paul, S. and Kumar, K. (2025) 'A Comprehensive Analysis on Online Food Delivery: Taste The Change', *International Journal of Research Publication and Reviews*, 6(5), pp. 5962–5970. https://ijrpr.com/uploads/V6ISSUE5/IJRPR45404.pdf
4. Swiggy (2026) *Restaurant listing endpoint.* https://www.swiggy.com/restaurants (accessed 19 September 2026).
