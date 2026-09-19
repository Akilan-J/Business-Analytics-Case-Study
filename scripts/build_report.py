"""Builds Case_Study_Report.pdf in the format prescribed in Section A."""
from pathlib import Path

import matplotlib
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
FIG, REP = ROOT / "report" / "figures", ROOT / "report"

# DejaVu carries the rupee sign; Helvetica does not.
fdir = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("DJV", fdir / "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DJV-B", fdir / "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DJV-I", fdir / "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFontFamily("DJV", normal="DJV", bold="DJV-B", italic="DJV-I")

INK, ACCENT, MUTED = colors.HexColor("#0b0b0b"), colors.HexColor("#2a78d6"), colors.HexColor("#52514e")
RULE, BAND = colors.HexColor("#dcdcd8"), colors.HexColor("#f2f5fa")

ss = getSampleStyleSheet()
def st(name, **kw):
    base = dict(fontName="DJV", fontSize=9.3, leading=12.6, textColor=INK, alignment=TA_JUSTIFY)
    base.update(kw)
    return ParagraphStyle(name, **base)

BODY    = st("body", spaceAfter=5)
H1      = st("h1", fontName="DJV-B", fontSize=13.2, leading=16.5, textColor=ACCENT,
             spaceBefore=11, spaceAfter=6, alignment=0)
H2      = st("h2", fontName="DJV-B", fontSize=10.8, leading=14, spaceBefore=9,
             spaceAfter=4, alignment=0)
TITLE   = st("title", fontName="DJV-B", fontSize=18, leading=23, alignment=0, spaceAfter=3)
SUB     = st("sub", fontSize=10.5, leading=15, textColor=MUTED, alignment=0, spaceAfter=2)
CAP     = st("cap", fontSize=7.8, leading=10, textColor=MUTED, alignment=1, spaceAfter=7)
BULLET  = st("bul", leftIndent=12, bulletIndent=2, spaceAfter=3)
CELL    = st("cell", fontSize=7.4, leading=9.6, alignment=0)
CELLB   = st("cellb", fontSize=7.4, leading=9.6, fontName="DJV-B", alignment=0)
SMALL   = st("small", fontSize=8.4, leading=11.6)

flow = []
def P(t, s=BODY): flow.append(Paragraph(t, s))
def H(t): flow.append(Paragraph(t, H1))
def h(t): flow.append(Paragraph(t, H2))
def S(h_=6): flow.append(Spacer(1, h_))
def B(items):
    for i in items:
        flow.append(Paragraph(i, BULLET, bulletText="•"))
    S(4)

def fig(name, caption, width=10.6*cm):
    p = FIG / f"{name}.png"
    from PIL import Image as PILImage
    w, hgt = PILImage.open(p).size
    img = Image(str(p), width=width, height=width * hgt / w)
    flow.append(KeepTogether([img, Paragraph(caption, CAP)]))

def table(rows, widths, header=True, band=True, align_right=()):
    data = []
    for ri, r in enumerate(rows):
        data.append([Paragraph(str(c), CELLB if (header and ri == 0) else CELL) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 3.5),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
             ("LEFTPADDING", (0, 0), (-1, -1), 5),
             ("RIGHTPADDING", (0, 0), (-1, -1), 5),
             ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), BAND),
                  ("LINEBELOW", (0, 0), (-1, 0), 0.9, ACCENT)]
    if band:
        for i in range(2, len(data), 2):
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafaf8")))
    t.setStyle(TableStyle(style))
    flow.append(t); S(9)

W = 17.0 * cm   # usable width

# ------------------------------------------------------------------ title
P("Intelligent Food Delivery Analytics<br/>Using Live Swiggy Market Intelligence", TITLE)
P("Business Analytics — Individual Case Study", SUB)
P("<b>Akilan J</b>  ·  Register Number: CB.SC.U4CSE23002  ·  Class/Section: CSE-A", SUB)
P("Data collected 19 September 2026 · 1,686 restaurants · 70 localities · 7 cities", SUB)
flow.append(Table([[""]], colWidths=[W], rowHeights=[2],
                  style=TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1.1, ACCENT)])))
S(10)

# ------------------------------------------------------------------ 1
H("1. Problem Statement and Objectives")
P("""Food delivery aggregators list thousands of restaurants whose ratings, pricing,
promised delivery times and promotional offers vary sharply from one locality to the
next. Neither the platform nor its restaurant partners has a clear, current view of
which of these attributes actually move customer-facing quality and delivery
performance. Because listings change continuously — offers rotate daily and promised
delivery times respond to live conditions — analyses built on static historical
extracts describe a market that no longer exists.""")
P("""This case study collects <b>live restaurant-level listing data directly from
Swiggy</b> across 70 localities in seven Indian metros and uses it to quantify the
drivers of restaurant rating and delivery time, to benchmark competing brands on
price, speed and promotion, and to segment restaurants by price–quality–speed
positioning.""")
h("Why this matters")
P("""Discounting is the most expensive lever a restaurant partner pulls and the most
visible one a platform subsidises; if it does not travel with better ratings, both
parties are funding something that does not buy loyalty. Equally, if delivery time is
driven by distance rather than by the restaurant, fixing it is a network-design problem
for the platform, not a kitchen problem for the partner.""")
h("Objectives")
B(["<b>Analyse the factors influencing food delivery performance</b> — isolate the "
   "contribution of last-mile distance, city and restaurant characteristics to "
   "promised delivery time.",
   "<b>Build predictive models</b> for delivery-time estimation and for restaurant "
   "rating, and establish how much of each is explainable from public listing data.",
   "<b>Benchmark competitors and segment the market</b> on price, rating, speed and "
   "promotional depth, and translate the segments into pricing and operational "
   "recommendations."])

# ------------------------------------------------------------------ 2
H("2. Data Collection and Dataset Description")
P("""<b>Source.</b> <font face="DJV-B">https://www.swiggy.com/dapi/restaurants/list/v5</font> —
the public JSON endpoint that renders swiggy.com/restaurants. It requires no login
and exposes only business listing attributes already shown to any visitor.""")
P("""<b>Procedure.</b> A purpose-built Python scraper (<font face="DJV-B">scripts/scrape_swiggy.py</font>)
issues one GET request per locality centroid for 70 localities — ten per city, spread
across each urban area so the sample is not dominated by a single high-income
catchment. A randomised 1.2–2.4 second delay separates requests. Each response is
walked for restaurant blocks and flattened to one row per restaurant × locality probe.""")
P("""<b>Unit of observation.</b> A restaurant listing exactly as a customer standing in
that locality would see it. The same restaurant can legitimately appear under several
localities; this is exploited as a <i>locality reach</i> feature before de-duplication.""")
table([["Property", "Value"],
       ["Collection date", "19 September 2026"],
       ["Cities", "Chennai, Bengaluru, Hyderabad, Mumbai, Delhi, Pune, Kolkata"],
       ["Localities probed", "70 (10 per city)"],
       ["Raw records", "1,831 restaurant × locality observations"],
       ["Unique restaurants", "1,686"],
       ["Attributes", "22 raw fields, 30 after feature engineering"],
       ["Records with a rating", "99.8%"],
       ["Authentication", "None — no login, no paid API, no personal data"]],
      [4.6*cm, W-4.6*cm])
h("Important variables")
table([["Variable", "Description", "Type"],
       ["avg_rating", "Average customer rating displayed on the listing (1–5)", "Continuous — target"],
       ["delivery_time_min", "Promised delivery time in minutes", "Continuous — target"],
       ["cost_for_two", "Indicative cost for two, parsed from '₹400 for two'", "Continuous"],
       ["last_mile_km", "Distance from the probed locality to the restaurant", "Continuous"],
       ["n_ratings", "Rating count, parsed from abbreviations such as '5.6K+'", "Continuous"],
       ["offer_type / offer_pct", "Offer mechanic and depth, parsed from header and sub-header", "Categorical / continuous"],
       ["cuisines", "Pipe-separated cuisine tags", "Multi-label"],
       ["chain_parent_id", "Brand identifier shared by outlets of one chain", "Categorical"],
       ["locality_reach", "Number of probed localities listing this restaurant", "Engineered count"],
       ["is_chain", "1 if the brand has ≥ 3 outlets in the sample", "Engineered binary"]],
      [3.5*cm, 9.6*cm, W-13.1*cm])
h("Compliance with the submission rules")
P("""No ready-made dataset from Kaggle, UCI or a GitHub dataset repository is used
anywhere in this study; the scraped data is the sole and primary dataset. The approved
proposal had planned to supplement live data with a historical Kaggle dataset and to
collect via the Apify Swiggy Scraper. Three changes were made during execution:""")
table([["Proposed", "Delivered", "Reason"],
       ["Historical Kaggle dataset + live data", "Live scraped data only",
        "Submission Instructions prohibit ready-made datasets as the primary source"],
       ["Apify Swiggy Scraper", "Purpose-built scraper on the same public endpoint",
        "Identical source and fields, no paid dependency, and the procedure is fully auditable in the repository"],
       ["Menu items and menu prices", "Not collected",
        "Swiggy's per-restaurant menu endpoint returns HTTP 202 to unauthenticated requests"],
       ["Google ratings, weather, traffic", "Not collected",
        "Not exposed by any public Swiggy endpoint"]],
      [4.6*cm, 4.9*cm, W-9.5*cm])
h("Ethics")
P("""Only publicly displayed business attributes are stored — no customer names,
reviews, addresses or personal identifiers. A randomised crawl delay limits load on
the source, and the data is used solely for this academic case study.""")

flow.append(PageBreak())

# ------------------------------------------------------------------ 3
H("3. Data Preparation and Exploratory Analysis")
h("Cleaning and preprocessing")
B(["<b>Display strings parsed to numbers.</b> <font face='DJV-B'>cost_for_two_raw</font> "
   "('₹400 for two') → 400; <font face='DJV-B'>total_ratings_raw</font> ('5.6K+') → 5,600.",
   "<b>Offers decomposed.</b> The header and sub-header together encode four distinct "
   "mechanics — capped percentage ('30% OFF, UPTO ₹60'), flat rupee ('₹85 OFF, ABOVE "
   "₹199'), item price point ('ITEMS AT ₹69') and none. Parsing only the header would "
   "have collapsed every price-point deal into an unusable 'ITEMS' label.",
   "<b>De-duplication.</b> 1,831 observations → 1,686 unique restaurants, after first "
   "deriving locality reach from the duplicate listings.",
   "<b>Outlier treatment.</b> Cost for two winsorised to the 1st–99th percentile "
   "(₹120–₹900); delivery times outside 5–120 minutes dropped.",
   "<b>Feature engineering.</b> Log cost, log rating count, cuisine count, chain size, "
   "chain flag, within-city cost percentile, offer depth and offer mechanic.",
   "<b>Missing data.</b> Only 4 restaurants (0.2%) lack a rating; these are excluded "
   "from rating models, leaving a modelling sample of 1,667."])
h("What the data shows")
fig("fig1_distributions", "Figure 1 — Ratings concentrate in a narrow 4.0–4.6 band; cost for two is right-skewed with a median of ₹300.")
P("""Ratings are compressed — the interquartile range spans roughly 0.3 of a star — so
there is little variance to explain, a modest R² on rating is expected, and small
coefficient effects remain commercially meaningful.""")
fig("fig3_price_vs_rating", "Figure 2 — Price and rating move in <i>opposite</i> directions (Spearman ρ = −0.24, p &lt; 0.001).")
P("""This is the study's first counter-intuitive result. Budget restaurants average
<b>4.41</b>, mid-priced <b>4.28</b> and premium <b>4.31</b>. Customers on a delivery
platform appear to rate against expectation rather than against absolute quality: a
₹200 meal that arrives correct and hot satisfies, while a ₹700 meal carries a heavier
burden of proof.""")
fig("fig2_delivery_by_city", "Figure 3 — Median promised delivery time by city: a 7-minute spread between Pune and the slowest cities.")
fig("fig5_offers_by_rating", "Figure 4 — Offer prevalence rises as rating falls (χ² = 15.8, df = 2, p = 0.0004).")
P("""Discounting is close to universal — 94.1% of restaurants display an active offer —
but it is <i>not</i> uniformly distributed. Restaurants rated below 3.8 are the most
likely to be discounting, and those rated above 4.2 the least.""")
P("""The most-listed cuisine tags are Desserts (838 listings), Beverages (515), Biryani
(327), Snacks (291) and Fast Food (263) — a dessert- and snack-heavy mix. The full cuisine
profile and the feature correlation matrix are in Appendix A (Figures A1 and A2).""")

flow.append(PageBreak())

# ------------------------------------------------------------------ 4
H("4. Analytics Method and Implementation")
P("""Five methods were applied, each chosen for a specific question. All models use a
fixed random seed (42), a 75/25 train–test split and 5-fold cross-validation.""")
table([["Question", "Method", "Justification"],
       ["What drives rating?", "Multiple linear regression (OLS, HC3 robust standard errors)",
        "Coefficients are directly interpretable as business levers and support significance testing"],
       ["Can a non-linear model do better?", "Random Forest, Gradient Boosting + permutation importance",
        "Captures interactions OLS misses; permutation importance gives an honest driver ranking"],
       ["Which restaurants are highly rated?", "Logistic regression, unweighted and class-weighted",
        "A classification framing management can act on, with a threshold-free metric (ROC-AUC)"],
       ["How do restaurants position themselves?", "K-Means with elbow and silhouette selection",
        "Unsupervised segmentation on price, quality and speed with no pre-imposed labels"],
       ["What drives delivery time?", "OLS + Random Forest + Gradient Boosting",
        "An interpretable minutes-per-km coefficient alongside the best achievable predictor"]],
      [3.9*cm, 5.3*cm, W-9.2*cm])

h("4.1 Multiple linear regression — drivers of rating")
P("""The model regresses average rating on log cost, log rating count, delivery time,
last-mile distance, cuisine count, locality reach, chain status, offer presence, offer
depth and city dummies (n = 1,667).""")
P("""<b>Diagnostics.</b> Variance inflation factors computed on the full design matrix
(including the intercept) peak at <b>2.67</b>, so multicollinearity is not a concern.
The Breusch–Pagan test rejects homoskedasticity (p = 1.8 × 10⁻¹¹), so HC3 robust
standard errors are reported. Adjusted R² = <b>0.260</b>. Residual and Q–Q plots are in
Appendix A (Figure A3).""")
P("""<b>Significant effects.</b> Log cost (−0.114), offer presence (−0.093), offer depth
(−0.002 per percentage point), delivery time (−0.008 per minute) and cuisine count
(−0.012) all reduce rating; last-mile distance carries a small positive coefficient
(+0.015). City effects are substantial — Kolkata +0.132, Pune −0.116, Hyderabad −0.094
relative to Bengaluru. Rating count and chain status are <i>not</i> significant.""")

h("4.2 Tree ensembles")
table([["Model", "CV R² (5-fold)", "Test R²", "Test RMSE", "Test MAE"],
       ["Linear Regression", "0.251", "0.261", "0.203", "0.163"],
       ["<b>Random Forest</b>", "<b>0.469</b>", "<b>0.487</b>", "<b>0.169</b>", "<b>0.131</b>"],
       ["Gradient Boosting", "0.442", "0.465", "0.173", "0.135"]],
      [5.0*cm, 3.2*cm, 2.8*cm, 3.0*cm, W-14.0*cm])
P("""Random Forest nearly doubles the linear model's explanatory power (R² 0.487 vs
0.261), confirming genuine non-linearity and interaction — but a mean absolute error of
0.131 stars against a distribution with an interquartile range of about 0.3 stars means
listing attributes still cannot substitute for knowing the food.""")
fig("fig8_importance", "Figure 5 — Permutation importance for the Random Forest rating model.", 10.6*cm)
P("""<b>Offer depth is the single most important feature</b>, ahead of price. This is the
study's central commercial finding and it is examined in Section 6.""")

h("4.3 Logistic regression — classifying highly rated restaurants")
P("""Target: rating ≥ 4.2, which covers 79.5% of the sample. Because the classes are
heavily imbalanced, both an unweighted and a class-weighted model were fitted.""")
table([["Model", "ROC-AUC", "Minority-class recall", "Accuracy"],
       ["Unweighted logistic", "0.728", "0.14", "0.81"],
       ["<b>Class-weighted logistic</b>", "0.726", "<b>0.59</b>", "0.68"]],
      [5.6*cm, 3.2*cm, 4.6*cm, W-13.4*cm])
P("""The unweighted model's 81% accuracy is misleading — it detects only 14% of
under-performing restaurants, which are precisely the ones a platform needs to find.
Class weighting raises minority recall to 59% at identical ROC-AUC, trading headline
accuracy for a model that is actually useful.""")
fig("fig9_roc", "Figure 6 — ROC curve for the class-weighted logistic model.", 8.0*cm)

h("4.4 K-Means — price–quality–speed segmentation")
P("""Segmentation on standardised log cost, rating, delivery time, log rating count and
offer depth. Silhouette scores are flat across k (0.205–0.234), indicating a continuum
rather than sharply separated groups; k = 4 was retained for interpretability and is
reported with that caveat (silhouette 0.215). Elbow and silhouette diagnostics are in
Appendix A (Figure A4).""")
table([["Segment", "n", "Rating", "Cost for two", "Delivery", "Offer depth", "% chain"],
       ["Value performer", "404", "<b>4.55</b>", "₹200", "25 min", "15.4%", "89%"],
       ["Premium performer", "442", "4.38", "₹400", "26 min", "1.3%", "80%"],
       ["Premium laggard", "267", "4.22", "₹400", "<b>35 min</b>", "4.6%", "62%"],
       ["Value laggard", "554", "<b>4.19</b>", "₹300", "28 min", "<b>62.9%</b>", "86%"]],
      [3.5*cm, 1.4*cm, 1.9*cm, 2.6*cm, 2.2*cm, 2.6*cm, W-14.2*cm])
fig("fig11_segments", "Figure 7 — The four segments on price and rating; marker shape and direct labels separate them.", 10.4*cm)
P("""The contrast between the two largest segments is the actionable one. <b>Value
performers</b> reach the highest rating in the sample (4.55) on the lowest price (₹200)
with only 15% average discount depth. <b>Value laggards</b> discount four times as
deeply (63%) and land at the lowest rating (4.19).""")

h("4.5 Predicting delivery time")
table([["Model", "CV R² (5-fold)", "Test R²", "Test RMSE (min)", "Test MAE (min)"],
       ["Linear Regression", "0.633", "0.613", "5.50", "4.18"],
       ["Random Forest", "0.694", "0.643", "5.28", "<b>3.93</b>"],
       ["<b>Gradient Boosting</b>", "0.692", "<b>0.651</b>", "<b>5.22</b>", "3.94"]],
      [5.0*cm, 3.2*cm, 2.6*cm, 3.4*cm, W-14.2*cm])
P("""Delivery time is far more predictable than rating (R² 0.651 vs 0.487) from the same
public fields. The interpretable OLS companion (R² 0.640) gives the headline operational
number: <b>each additional kilometre of last-mile distance adds 3.43 minutes</b>
(p &lt; 0.001). Higher-rated restaurants are also faster (−5.72 minutes per rating point),
and chains are about 1.2 minutes quicker than independents.""")
fig("fig12_delivery_model", "Figure 8 — Actual vs predicted delivery time, and minutes added per kilometre by city.", 11.2*cm)
fig("fig13_delivery_importance", "Figure 9 — Permutation importance for the delivery-time model; distance dominates.", 10.6*cm)

h("4.6 Competitor benchmarking")
P("""Outlets were rolled up to the brand so that multi-outlet operators are compared as
competitors rather than as individual listings. Fifteen brands with five or more outlets
qualify.""")
fig("fig14_benchmark", "Figure 10 — Competitor benchmark: median delivery time against average rating; bubble size is outlet count.", 10.6*cm)
table([["Brand", "Outlets", "Cities", "Rating", "Cost for two", "Delivery", "% with offer"],
       ["NIC Ice Creams", "35", "6", "<b>4.65</b>", "₹120", "23 min", "100%"],
       ["The Belgian Waffle Co.", "47", "7", "4.53", "₹200", "28 min", "98%"],
       ["Baskin Robbins", "59", "7", "4.52", "₹250", "24 min", "100%"],
       ["Theobroma", "44", "5", "4.49", "₹400", "<b>19 min</b>", "100%"],
       ["Domino's Pizza", "51", "7", "4.35", "₹400", "25 min", "100%"],
       ["McDonald's", "55", "7", "4.34", "₹400", "26 min", "100%"],
       ["Subway", "51", "7", "4.23", "₹350", "24 min", "88%"],
       ["Burger King", "42", "7", "4.20", "₹350", "27 min", "100%"],
       ["Pizza Hut", "46", "6", "4.18", "₹350", "29.5 min", "100%"],
       ["KFC", "58", "7", "<b>4.14</b>", "₹400", "26 min", "100%"]],
      [4.3*cm, 1.8*cm, 1.6*cm, 1.8*cm, 2.6*cm, 2.2*cm, W-14.3*cm])
P("""The dessert and beverage brands occupy the favourable quadrant — faster and better
rated — while the large QSR burger and pizza chains cluster lower despite comparable
delivery times. Theobroma is the standout on speed at 19 minutes.""")

# ------------------------------------------------------------------ 5
H("5. Comparison with State-of-the-Art Methods")
P("""Four recent published studies on the same problem family were compared. The
comparison focuses on method, dataset, evaluation approach, findings, strengths and
limitations. <b>Reported scores are not directly comparable across rows</b>: each study
uses a different dataset, target variable, feature set and split, so a higher number
does not by itself indicate a better method.""")
table([["Published Study / Year", "Dataset", "Method Used", "Evaluation Metric",
        "Key Result", "Comparison with Your Work"],
       ["Garg, Ayaan, Parekh &amp; Udandarao (2025), arXiv:2503.15177",
        "Food delivery dataset for Indian cities; includes traffic, weather, events and geospatial coordinates",
        "Linear Regression, Decision Tree, Bagging, Random Forest, XGBoost, LightGBM",
        "R², MSE",
        "LightGBM best: R² = 0.76, MSE = 20.59",
        "Closest comparator to our §4.5. Their higher R² (0.76 vs 0.651) rests on traffic, weather and event features no public Swiggy endpoint exposes — a feature-availability gap, not a method gap. We achieve MAE 3.94 min from listing data alone and add an interpretable operational coefficient (3.43 min/km) they do not report."],
       ["Turai, Praneetha, Aishwarya, Adil &amp; Vangala (2025), WJARR 25(02), 1039–1046",
        "Zomato restaurant and review dataset (secondary)",
        "K-Means and Hierarchical clustering into 3 groups by cuisine and price; sentiment via Logistic Regression, Decision Tree, Naive Bayes, LDA",
        "Clustering groups; classification accuracy",
        "Logistic Regression and LightGBM performed best for sentiment; restaurants grouped into 3 cuisine–price segments",
        "Same segmentation family as our §4.4, but they cluster on cuisine and price only and fix k = 3 with no stated selection criterion. We select k by elbow and silhouette, report it honestly (0.215, a continuum), and add speed and offer depth — which is what surfaces the Value-laggard segment. Lacking review text, we cannot replicate their sentiment analysis."],
       ["Raj, Paul &amp; Kumar (2025), IJRPR 6(5), 5962–5970",
        "Zomato restaurant and user data (secondary)",
        "SQL + Python + Power BI + Excel; EDA and logistic regression",
        "Descriptive; no held-out predictive evaluation reported",
        "Identified factors influencing ratings, cuisine popularity and location effects",
        "Similar descriptive ambition to our §3, but it stops at dashboards with no held-out validation. We carry the same questions into tested models with train/test splits and cross-validation, and quantify effects (ρ = −0.24 price vs rating; χ² = 15.8 offers vs rating band)."],
       ["Kulkarni, Bhandari &amp; Bhoite (2019), IJCATR 8(9), 375–378",
        "Zomato restaurants dataset (secondary)",
        "SVM, Linear Regression, Decision Tree, Random Forest, XGBoost, AdaBoost",
        "Accuracy (83%)",
        "AdaBoost achieved 83%",
        "The foundational rating-prediction reference, but a single accuracy figure with no RMSE/MAE and no clear regression-vs-classification distinction is hard to interpret. We report CV R², test R², RMSE and MAE, plus ROC-AUC with per-class recall — surfacing the imbalance problem (unweighted recall 0.14) a bare accuracy number conceals."]],
      [2.9*cm, 2.5*cm, 2.7*cm, 2.1*cm, 2.4*cm, W-12.6*cm])
h("What this comparison establishes")
B(["<b>Every comparator uses a secondary dataset</b> — Zomato extracts or a compiled "
   "delivery dataset. This study is the only one of the five built on primary data "
   "collected first-hand, which is what the submission rules require and what makes "
   "the locality-level analysis possible.",
   "<b>Our delivery-time R² (0.651) is lower than Garg et al.'s 0.76, and this is "
   "expected</b>: they include traffic and weather, which are the dominant sources of "
   "real-world delivery variance and are unavailable publicly. The gap is a feature "
   "availability gap, not a method gap.",
   "<b>No comparator examines discount depth against rating.</b> The negative "
   "association reported in Section 6 is the contribution that does not appear in the "
   "prior work reviewed here."])

flow.append(PageBreak())

# ------------------------------------------------------------------ 6
H("6. Results, Business Insights and Recommendations")
h("Consolidated results")
table([["Metric", "Value"],
       ["Restaurant × locality observations scraped", "1,831"],
       ["Unique restaurants after de-duplication", "1,686"],
       ["Cities / localities covered", "7 / 70"],
       ["Median cost for two", "₹300"],
       ["Median promised delivery time", "27 min"],
       ["Restaurants running a visible offer", "94.1%"],
       ["Rating model — OLS adjusted R²", "0.260"],
       ["Rating model — Random Forest test R²", "0.487"],
       ["High-rating classifier — ROC-AUC (class-weighted)", "0.726"],
       ["Delivery-time model — Gradient Boosting test R²", "0.651 (MAE 3.94 min)"],
       ["Minutes added per extra km of last mile", "3.43"],
       ["K-Means segments (k = 4) — silhouette", "0.215"]],
      [10.0*cm, W-10.0*cm])

h("Insight 1 — Deep discounting travels with lower ratings, not higher ones")
P("""Restaurants running a discount of 50% or more average <b>4.23</b> against
<b>4.39</b> for everyone else — a gap of 0.16 stars on a scale where the interquartile
range is roughly 0.3 (Welch t = −13.3, p &lt; 0.001). Offer depth is also the highest-ranked
permutation-importance feature in the Random Forest rating model, and the χ² test confirms
that offer prevalence and rating band are not independent (χ² = 15.8, p = 0.0004).""")
P("""<b>This is an association, not proof of causation</b>, and the more likely direction
runs the other way: restaurants that are struggling discount to buy volume. Either way the
operational implication holds — <i>discount depth is a reliable distress signal, not a
quality signal</i>.""")
h("Insight 2 — Price and rating are inversely related")
P("""Spearman ρ = −0.24 (p &lt; 0.001); budget restaurants average 4.41 against 4.31 for
premium. Controlling for everything else, a one-log-unit increase in cost costs 0.114
rating points. Customers appear to rate against expectation, and premium positioning
carries a heavier burden of proof on a delivery platform than in a dine-in setting.""")
h("Insight 3 — Delivery performance is a network problem, not a kitchen problem")
P("""Distance overwhelmingly dominates the delivery-time model, adding <b>3.43 minutes per
kilometre</b>. City effects are large and independent of distance — Pune is roughly 10
minutes faster than Kolkata at equal last-mile distance — which points at fleet density
and city operations rather than at restaurant preparation.""")
h("Insight 4 — Rating is only half-explainable from listing data")
P("""The best rating model reaches R² 0.487 while the delivery model reaches 0.651 on the
same fields. Roughly half of rating variance lives in food quality, packaging and service
consistency, which no listing attribute captures. Any platform system that ranks or
promotes restaurants on listing metadata alone is working with half the picture.""")

h("Recommendations")
h("For the platform")
B(["<b>Treat discount depth as a risk indicator.</b> Route restaurants sustaining ≥50% "
   "discounts into a quality review rather than into further promotional subsidy. The "
   "554-strong Value-laggard segment (63% average depth, 4.19 rating) is the target list.",
   "<b>Deploy the class-weighted classifier, not the accurate-looking one.</b> At 59% "
   "minority recall it identifies more than four times as many under-performing "
   "restaurants as the unweighted model at the same ROC-AUC.",
   "<b>Attack delivery through network design.</b> At 3.43 minutes per kilometre, "
   "shrinking the median last mile is worth more than any restaurant-side intervention. "
   "Prioritise Kolkata, Hyderabad and Bengaluru, which sit 4–7 minutes above Pune.",
   "<b>Stop ranking on listing metadata alone.</b> With R² 0.487 the platform should feed "
   "order-level outcomes — cancellations, complaints, reorder rate — into any quality score."])
h("For restaurant partners")
B(["<b>Do not buy rating with discounts.</b> Value performers hit 4.55 on ₹200 with 15% "
   "average depth; Value laggards spend 63% to reach 4.19. The spend is not converting.",
   "<b>Price to the delivery context.</b> Premium positioning attracts a harsher rating "
   "response; either justify it visibly or compete in the value tier where ratings run higher.",
   "<b>Fix speed before menu breadth.</b> Each minute of promised delivery time costs "
   "0.008 rating points, and every additional cuisine tag costs 0.012 — breadth reads as "
   "lack of focus.",
   "<b>Benchmark against the right quadrant.</b> Theobroma (19 min, 4.49) and NIC Ice "
   "Creams (23 min, 4.65) show the achievable frontier for speed and rating together."])

# ------------------------------------------------------------------ 7
H("7. Conclusion")
P("""This study built a primary dataset of 1,686 restaurants across 70 localities and
seven Indian metros by scraping Swiggy's public listing endpoint, and used it to model
restaurant rating and delivery time, benchmark fifteen competing brands and segment the
market on price, quality and speed.""")
P("""The central outcome is that <b>the two questions a food delivery business cares about
are not equally answerable from public data</b>. Delivery time is well explained
(R² 0.651, MAE under four minutes) and reduces to a network-design problem — 3.43 minutes
per kilometre, with large city effects. Rating is only half explained (R² 0.487), because
the half that matters lives in food and service quality that listings do not expose.""")
P("""The most commercially significant finding is that <b>promotional depth is negatively
associated with rating</b> — restaurants discounting 50% or more average 0.16 stars lower —
and that offer depth outranks price as a predictor of rating. None of the four comparator
studies examines this relationship. For a platform that subsidises discounting and for
partners who fund it, the implication is that deep promotion should be read as a signal
that something needs fixing, not as a lever that fixes it.""")
h("Limitations")
B(["<b>Cross-sectional snapshot.</b> A single collection on 19 September 2026 cannot "
   "separate cause from effect; the discount–rating association is consistent with "
   "struggling restaurants discounting, which is the more plausible direction.",
   "<b>Promised, not actual, delivery time.</b> The endpoint exposes Swiggy's estimate, "
   "which already embeds the platform's own modelling — real delivery variance is unobserved.",
   "<b>No traffic, weather or menu data</b>, which limits direct comparison with Garg et al. (2025).",
   "<b>Weak cluster separation.</b> A silhouette of 0.215 means the four segments describe "
   "a continuum; they are useful as management labels, not as natural kinds.",
   "<b>Listing-position bias.</b> The endpoint returns roughly 28 restaurants per locality "
   "in Swiggy's own ranking order, so the sample skews toward restaurants the platform "
   "already promotes."])
h("Future work")
P("""Repeated collection over several weeks would turn this cross-section into a panel and
allow the discount–rating question to be tested causally — observing whether a rating falls
after a restaurant deepens its discount, or the discount deepens after the rating falls.""")

H("References")
refs = [
 "Garg, A., Ayaan, M., Parekh, S. and Udandarao, V. (2025) <i>Food Delivery Time Prediction in Indian Cities Using Machine Learning Models.</i> arXiv:2503.15177. Available at: https://arxiv.org/abs/2503.15177",
 "Turai, S., Praneetha, P., Aishwarya, R. B., Adil, M. and Vangala, M. C. (2025) 'Analysis of restaurant ratings and reviews using machine learning', <i>World Journal of Advanced Research and Reviews</i>, 25(02), pp. 1039–1046. doi: 10.30574/wjarr.2025.25.2.0378",
 "Raj, H., Paul, S. and Kumar, K. (2025) 'A Comprehensive Analysis on Online Food Delivery: Taste The Change', <i>International Journal of Research Publication and Reviews</i>, 6(5), pp. 5962–5970.",
 "Kulkarni, A., Bhandari, D. and Bhoite, S. (2019) 'Restaurants Rating Prediction using Machine Learning Algorithms', <i>International Journal of Computer Applications Technology and Research</i>, 8(9), pp. 375–378.",
 "Swiggy (2026) <i>Restaurant listing endpoint.</i> Available at: https://www.swiggy.com/restaurants (Accessed: 19 September 2026).",
 "Pedregosa, F. et al. (2011) 'Scikit-learn: Machine Learning in Python', <i>Journal of Machine Learning Research</i>, 12, pp. 2825–2830.",
 "Seabold, S. and Perktold, J. (2010) 'statsmodels: Econometric and statistical modeling with Python', <i>Proceedings of the 9th Python in Science Conference</i>.",
]
for i, r in enumerate(refs, 1):
    flow.append(Paragraph(f"[{i}]&nbsp;&nbsp;{r}", SMALL))
    S(3)

H("Appendix A — Supporting Figures")
fig("fig4_cuisines", "Figure A1 — Most-listed cuisine tags across the 1,686 restaurants.", 11.9*cm)
fig("fig6_corr", "Figure A2 — Correlation matrix of the modelling features.", 10.4*cm)
fig("fig7_ols_diagnostics", "Figure A3 — Residual and Q\u2013Q diagnostics for the OLS rating model.", 11.9*cm)
fig("fig10_k_selection", "Figure A4 — Elbow and silhouette diagnostics for k selection in the K-Means segmentation.", 11.9*cm)

H("Appendix B — City Profile")
table([["City", "Restaurants", "Median cost", "Mean rating", "Median delivery", "% with offer", "% chain"],
       ["Chennai", "242", "\u20b9350", "4.34", "25 min", "96%", "95%"],
       ["Delhi", "223", "\u20b9350", "4.35", "26 min", "97%", "94%"],
       ["Mumbai", "269", "\u20b9350", "4.37", "28 min", "96%", "75%"],
       ["Pune", "241", "\u20b9350", "4.26", "23 min", "96%", "78%"],
       ["Bengaluru", "253", "\u20b9300", "4.34", "30 min", "86%", "80%"],
       ["Hyderabad", "231", "\u20b9300", "4.22", "30 min", "95%", "75%"],
       ["Kolkata", "227", "\u20b9300", "4.43", "30 min", "92%", "70%"]],
      [3.0*cm, 2.3*cm, 2.4*cm, 2.4*cm, 2.8*cm, 2.3*cm, W-15.2*cm])

H("Appendix C — Offer Mechanics")
table([["Offer mechanic", "Share of restaurants", "Mean rating", "Median cost for two"],
       ["Item price point (e.g. 'ITEMS AT \u20b969')", "44.7%", "4.38", "\u20b9350"],
       ["Capped percentage (e.g. '30% OFF UPTO \u20b960')", "43.7%", "4.26", "\u20b9300"],
       ["Flat rupee (e.g. '\u20b985 OFF ABOVE \u20b9199')", "5.5%", "4.38", "\u20b9350"],
       ["No visible offer", "5.9%", "<b>4.45</b>", "\u20b9350"]],
      [7.2*cm, 3.6*cm, 2.7*cm, W-13.5*cm])
P("""Restaurants running no visible offer at all record the <i>highest</i> mean rating in
the sample (4.45), and percentage-discount restaurants the lowest (4.26) \u2014 consistent
with the discount\u2013rating association reported in Section 6.""", SMALL)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("DJV", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(2.0*cm, 1.15*cm, "Akilan J · Business Analytics Individual Case Study · Swiggy Live Market Intelligence")
    canvas.drawRightString(A4[0]-2.0*cm, 1.15*cm, f"{doc.page}")
    canvas.setStrokeColor(RULE)
    canvas.line(2.0*cm, 1.5*cm, A4[0]-2.0*cm, 1.5*cm)
    canvas.restoreState()

out = ROOT / "Case_Study_Report.pdf"
SimpleDocTemplate(str(out), pagesize=A4,
                  leftMargin=2.0*cm, rightMargin=2.0*cm,
                  topMargin=1.7*cm, bottomMargin=2.0*cm,
                  title="Intelligent Food Delivery Analytics Using Live Swiggy Market Intelligence",
                  author="Akilan J").build(flow, onFirstPage=footer, onLaterPages=footer)
print("wrote", out)
