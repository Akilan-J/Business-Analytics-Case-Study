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
    base = dict(fontName="DJV", fontSize=8.9, leading=11.8, textColor=INK, alignment=TA_JUSTIFY)
    base.update(kw)
    return ParagraphStyle(name, **base)

BODY    = st("body", spaceAfter=4)
H1      = st("h1", fontName="DJV-B", fontSize=11.8, leading=14.5, textColor=ACCENT,
             spaceBefore=8, spaceAfter=4.5, alignment=0)
H2      = st("h2", fontName="DJV-B", fontSize=9.6, leading=12.4, spaceBefore=6,
             spaceAfter=3, alignment=0)
TITLE   = st("title", fontName="DJV-B", fontSize=15, leading=19, alignment=0, spaceAfter=2)
SUB     = st("sub", fontSize=10.5, leading=15, textColor=MUTED, alignment=0, spaceAfter=2)
CAP     = st("cap", fontSize=7.8, leading=10, textColor=MUTED, alignment=1, spaceAfter=7)
BULLET  = st("bul", leftIndent=12, bulletIndent=2, spaceAfter=3)
CELL    = st("cell", fontSize=6.9, leading=8.7, alignment=0)
CELLB   = st("cellb", fontSize=6.9, leading=8.7, fontName="DJV-B", alignment=0)
SMALL   = st("small", fontSize=8.4, leading=11.6)

flow = []
def P(t, s=BODY): flow.append(Paragraph(t, s))
def H(t): flow.append(Paragraph(t, H1))
def h(t): flow.append(Paragraph(t, H2))
def S(h_=5): flow.append(Spacer(1, h_))
def B(items):
    for i in items:
        flow.append(Paragraph(i, BULLET, bulletText="•"))
    S(3)

def fig(name, caption, width=9.6*cm):
    from PIL import Image as PILImage
    p = FIG / f"{name}.png"
    w, hgt = PILImage.open(p).size
    img = Image(str(p), width=width, height=width * hgt / w)
    flow.append(KeepTogether([img, Paragraph(caption, CAP)]))

def table(rows, widths, header=True, band=True):
    data = [[Paragraph(str(c), CELLB if (header and ri == 0) else CELL) for c in r]
            for ri, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0,0), (-1,-1), "TOP"),
             ("TOPPADDING", (0,0), (-1,-1), 2.6), ("BOTTOMPADDING", (0,0), (-1,-1), 2.6),
             ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4),
             ("LINEBELOW", (0,0), (-1,-2), 0.4, RULE)]
    if header:
        style += [("BACKGROUND", (0,0), (-1,0), BAND), ("LINEBELOW", (0,0), (-1,0), 0.8, ACCENT)]
    if band:
        for i in range(2, len(data), 2):
            style.append(("BACKGROUND", (0,i), (-1,i), colors.HexColor("#fafaf8")))
    t.setStyle(TableStyle(style)); flow.append(t); S(7)

W = 17.0 * cm

# ---------------------------------------------------------------- title
P("Intelligent Food Delivery Analytics Using Live Swiggy Market Intelligence", TITLE)
P("23CSE452 Business Analytics — Individual Case Study", SUB)
P("<b>Akilan J</b> · CB.SC.U4CSE23002 · CSE-A · Data collected 19 September 2026", SUB)
flow.append(Table([[""]], colWidths=[W], rowHeights=[2],
                  style=TableStyle([("LINEBELOW",(0,0),(-1,-1),1.0,ACCENT)])))
S(8)

# ---------------------------------------------------------------- 1
H("1. Problem statement and objectives")
P("""Food delivery aggregators list thousands of restaurants whose ratings, prices,
promised delivery times and promotional offers vary sharply from one locality to the
next. Neither the platform nor its restaurant partners has a current view of which of
these attributes actually move customer-facing quality or delivery performance, and
because listings change daily, analyses built on static historical extracts describe a
market that no longer exists.""")
P("""Two decisions hang on this. Discounting is the most expensive lever a partner pulls
and the most visible one a platform subsidises — if it does not travel with better
ratings, both are funding something that does not buy loyalty. And if delivery time is
driven by distance rather than by the restaurant, fixing it is a network-design problem
for the platform, not a kitchen problem for the partner.""")
h("Objectives")
B(["<b>Identify the drivers of restaurant rating</b> from publicly listed attributes, and "
   "establish how much of rating is explainable from listing data at all.",
   "<b>Model promised delivery time</b> and separate the contribution of last-mile "
   "distance from restaurant and city effects.",
   "<b>Benchmark competitors and segment the market</b> on price, rating, speed and "
   "discount depth, and convert the segments into pricing and operational recommendations."])

# ---------------------------------------------------------------- 2
H("2. Dataset source and collection method")
P("""<b>Collection method: web scraping.</b> Data was collected from
<font face="DJV-B">www.swiggy.com/dapi/restaurants/list/v5</font>, the public JSON endpoint
that renders swiggy.com/restaurants. It requires no login and exposes only business
listing attributes already shown to any visitor. A purpose-built Python scraper
(<font face="DJV-B">scripts/scrape_swiggy.py</font>) issues one request per locality centroid
for 70 localities — ten per city, spread across each urban area so the sample is not
dominated by one high-income catchment — with a randomised 1.2–2.4 s delay between
requests. Each response is flattened to one row per restaurant × locality probe.""")
table([["Property", "Value", "Property", "Value"],
       ["Records collected", "1,831 restaurant × locality rows", "Unique restaurants", "1,686"],
       ["Cities / localities", "7 / 70", "Attributes", "22 raw, 30 engineered"],
       ["Records with a rating", "99.8%", "Authentication", "None; no personal data"]],
      [3.2*cm, 5.3*cm, 3.2*cm, W-11.7*cm])
h("Important variables")
table([["Variable", "Meaning", "Variable", "Meaning"],
       ["avg_rating", "Displayed rating, 1–5 (target)", "delivery_time_min", "Promised delivery time (target)"],
       ["cost_for_two", "Indicative price, from '₹400 for two'", "last_mile_km", "Distance from the probed locality"],
       ["n_ratings", "Rating count, from '5.6K+'", "offer_type / offer_pct", "Offer mechanic and depth"],
       ["cuisines", "Pipe-separated cuisine tags", "is_chain", "Brand has ≥ 3 outlets in sample"]],
      [2.8*cm, 5.7*cm, 3.0*cm, W-11.5*cm])
P("""No ready-made Kaggle, UCI or GitHub dataset is used; the scraped data is the sole and
primary dataset. The approved proposal had planned to add a historical Kaggle dataset and
to collect via the Apify Swiggy Scraper. The Kaggle component was dropped because the
course rules prohibit ready-made datasets as the primary source, and collection was done
with an auditable in-repository scraper against the same public endpoint. Menu prices,
Google ratings, weather and traffic were planned but are not obtainable — Swiggy's menu
endpoint returns HTTP 202 to unauthenticated requests and the rest are not exposed
publicly. <b>Ethics:</b> only business attributes are stored — no customer names, reviews
or identifiers — and a crawl delay limits load on the source.""")

# ---------------------------------------------------------------- 3
H("3. Data preparation and exploratory analysis")
B(["<b>Display strings parsed to numbers:</b> '₹400 for two' → 400; '5.6K+' → 5,600.",
   "<b>Offers decomposed</b> from header and sub-header into four mechanics — capped "
   "percentage ('30% OFF UPTO ₹60'), flat rupee ('₹85 OFF ABOVE ₹199'), item price point "
   "('ITEMS AT ₹69') and none. Parsing the header alone would collapse every price-point "
   "deal into an unusable 'ITEMS' label.",
   "<b>De-duplicated</b> 1,831 rows → 1,686 restaurants, after first deriving locality "
   "reach from the duplicates. <b>Outliers</b> winsorised (cost ₹120–₹900); delivery times "
   "outside 5–120 min dropped. <b>Missing:</b> 4 restaurants (0.2%) lack a rating and are "
   "excluded from rating models, leaving 1,667."])
fig("fig3_price_vs_rating", "Figure 1 — Price and rating move in <i>opposite</i> directions (Spearman ρ = −0.24, p &lt; 0.001).")
P("""Budget restaurants average <b>4.41</b>, mid-priced 4.28 and premium 4.31. Customers
appear to rate against expectation: a ₹200 meal that arrives hot and correct satisfies,
while a ₹700 meal carries a heavier burden of proof. Ratings are also compressed — the
interquartile range spans about 0.3 of a star — so a modest R² on rating is expected and
small coefficient effects remain commercially meaningful.""")
fig("fig5_offers_by_rating", "Figure 2 — Offer prevalence rises as rating falls (χ² = 15.8, df = 2, p = 0.0004).")
P("""Discounting is near-universal — 94.1% of restaurants display an active offer — but it
is not evenly spread. Restaurants rated below 3.8 are the most likely to be discounting and
those above 4.2 the least. Median cost for two is ₹300 and median promised delivery 27
minutes; Pune is the fastest city at 23 minutes and Kolkata, Hyderabad and Bengaluru the
slowest at 30.""")

# ---------------------------------------------------------------- 4
H("4. Analytics method and implementation")
P("""Five methods from the Business Analytics syllabus were applied. All use a fixed seed
(42), a 75/25 train–test split and 5-fold cross-validation.""")
table([["Question", "Method", "Justification"],
       ["What drives rating?", "Multiple linear regression (OLS, HC3 robust SEs)",
        "Coefficients are interpretable as business levers and support significance testing"],
       ["Can a non-linear model do better?", "Random Forest, Gradient Boosting + permutation importance",
        "Captures interactions OLS misses; permutation importance ranks drivers honestly"],
       ["Which restaurants are highly rated?", "Logistic regression, unweighted and class-weighted",
        "A classification framing management can act on, with threshold-free ROC-AUC"],
       ["How do restaurants position?", "K-Means, k by elbow and silhouette",
        "Unsupervised segmentation with no pre-imposed labels"],
       ["What drives delivery time?", "OLS + Random Forest + Gradient Boosting",
        "An interpretable minutes-per-km coefficient plus the best achievable predictor"]],
      [3.4*cm, 4.9*cm, W-8.3*cm])
h("4.1 Rating models")
P("""Rating was regressed on log cost, log rating count, delivery time, last-mile distance,
cuisine count, locality reach, chain status, offer presence, offer depth and city dummies
(n = 1,667). VIFs computed on the full design matrix peak at <b>2.67</b>, so
multicollinearity is not a concern; Breusch–Pagan rejects homoskedasticity
(p = 1.8 × 10⁻¹¹) so HC3 robust standard errors are used. Significant effects: log cost
−0.114, offer presence −0.093, delivery time −0.008/min, cuisine count −0.012; city effects
are large (Kolkata +0.132, Pune −0.116). Rating count and chain status are not significant.""")
table([["Rating model", "CV R²", "Test R²", "RMSE", "MAE"],
       ["Linear Regression", "0.251", "0.261", "0.203", "0.163"],
       ["<b>Random Forest</b>", "<b>0.469</b>", "<b>0.487</b>", "<b>0.169</b>", "<b>0.131</b>"],
       ["Gradient Boosting", "0.442", "0.465", "0.173", "0.135"]],
      [5.0*cm, 2.6*cm, 2.6*cm, 2.6*cm, W-12.8*cm])
fig("fig8_importance", "Figure 3 — Permutation importance, Random Forest rating model: offer depth outranks price.", 9.2*cm)
P("""Random Forest nearly doubles the linear model's explanatory power, confirming genuine
non-linearity — but MAE 0.131 stars against an interquartile range of ~0.3 means listing
attributes cannot substitute for knowing the food. A logistic model for rating ≥ 4.2
(79.5% of the sample) reaches ROC-AUC <b>0.726</b>; crucially, the unweighted version's 81%
accuracy conceals just <b>14%</b> recall on under-performers, while class weighting raises
that to <b>59%</b> at the same AUC — the usable model for a platform hunting weak listings.""")
h("4.2 Segmentation and competitor benchmarking")
P("""K-Means on standardised log cost, rating, delivery time, log rating count and offer
depth. Silhouette is flat across k (0.205–0.234), indicating a continuum rather than sharply
separated groups; k = 4 was retained for interpretability and is reported with that caveat
(silhouette 0.215).""")
table([["Segment", "n", "Rating", "Cost for two", "Delivery", "Offer depth", "% chain"],
       ["Value performer", "404", "<b>4.55</b>", "₹200", "25 min", "15.4%", "89%"],
       ["Premium performer", "442", "4.38", "₹400", "26 min", "1.3%", "80%"],
       ["Premium laggard", "267", "4.22", "₹400", "<b>35 min</b>", "4.6%", "62%"],
       ["Value laggard", "554", "<b>4.19</b>", "₹300", "28 min", "<b>62.9%</b>", "86%"]],
      [3.3*cm, 1.3*cm, 1.8*cm, 2.4*cm, 2.0*cm, 2.4*cm, W-13.2*cm])
fig("fig11_segments", "Figure 4 — The four segments on price and rating; shape and direct labels separate them.", 9.4*cm)
fig("fig14_benchmark", "Figure 5 — Competitor benchmark of 15 multi-outlet brands; bubble size is outlet count.", 10.0*cm)
P("""Outlets were rolled up to the brand so multi-outlet operators compare as competitors.
Dessert and beverage brands hold the favourable quadrant — NIC Ice Creams (4.65, 23 min),
Theobroma (4.49, <b>19 min</b>), Baskin Robbins (4.52, 24 min) — while the large burger and
pizza chains cluster lower on rating at comparable speed (KFC 4.14, Pizza Hut 4.18,
Burger King 4.20) despite all running offers on essentially every outlet.""")
h("4.3 Delivery-time model")
table([["Delivery model", "CV R²", "Test R²", "RMSE (min)", "MAE (min)"],
       ["Linear Regression", "0.633", "0.613", "5.50", "4.18"],
       ["Random Forest", "0.694", "0.643", "5.28", "<b>3.93</b>"],
       ["<b>Gradient Boosting</b>", "0.692", "<b>0.651</b>", "<b>5.22</b>", "3.94"]],
      [5.0*cm, 2.6*cm, 2.6*cm, 3.0*cm, W-13.2*cm])
fig("fig12_delivery_model", "Figure 6 — Actual vs predicted delivery time, and minutes added per kilometre by city.", 12.0*cm)
P("""Delivery time is far more predictable than rating from the same fields. The
interpretable OLS companion (R² 0.640) gives the operational number: <b>each extra kilometre
of last mile adds 3.43 minutes</b> (p &lt; 0.001). Higher-rated restaurants are also faster
(−5.72 min per rating point) and chains about 1.2 minutes quicker than independents. City
effects are large and independent of distance — Pune is roughly 10 minutes faster than
Kolkata at equal last-mile distance.""")

# ---------------------------------------------------------------- 5
H("5. Comparison with three published studies")
P("""Three recent published studies on the same problem family are compared below.
<b>Reported scores are not directly comparable across rows</b>: each study uses a different
dataset, target variable, feature set and experimental setting, so a higher number does not
by itself indicate a better method.""")
table([["Published Study / Year", "Dataset", "Method Used", "Evaluation Metric", "Key Result",
        "Comparison with Your Work"],
       ["Garg, Ayaan, Parekh &amp; Udandarao (2025), arXiv:2503.15177",
        "Indian-city food delivery dataset with traffic, weather, events and geospatial coordinates (secondary)",
        "Linear Regression, Decision Tree, Bagging, Random Forest, XGBoost, LightGBM",
        "R², MSE", "LightGBM best: R² = 0.76, MSE = 20.59",
        "Closest comparator to §4.3. Their higher R² rests on traffic, weather and event features that no public Swiggy endpoint exposes — a feature-availability gap, not evidence of a better method. We reach MAE 3.94 min from listing data alone and add an interpretable operational coefficient (3.43 min/km) they do not report. Strength: their richer feature set. Limitation: not reproducible from public data."],
       ["Turai, Praneetha, Aishwarya, Adil &amp; Vangala (2025), WJARR 25(02), 1039–1046",
        "Zomato restaurant and review data (secondary)",
        "K-Means and Hierarchical clustering (k = 3) on cuisine and price; sentiment via Logistic Regression, Decision Tree, Naive Bayes, LDA",
        "Cluster groups; classification accuracy",
        "Logistic Regression and LightGBM best for sentiment; 3 cuisine–price segments",
        "Same segmentation family as §4.2, but they cluster on cuisine and price only and fix k = 3 with no stated selection criterion. We select k by elbow and silhouette and report it honestly (0.215, a continuum), and add delivery speed and offer depth — which is what surfaces the Value-laggard segment. Strength: they have review text for sentiment, which we lack. Limitation: no validation of cluster count."],
       ["Raj, Paul &amp; Kumar (2025), IJRPR 6(5), 5962–5970",
        "Zomato restaurant and user data (secondary)",
        "SQL, Python, Power BI and Excel; EDA with logistic regression",
        "Descriptive; no held-out predictive evaluation reported",
        "Identified factors influencing ratings, cuisine popularity and location effects",
        "Similar descriptive ambition to §3, but the study stops at dashboards with no held-out validation, so its claims cannot be checked. We carry the same questions into tested models with train/test splits and cross-validation, and quantify effects (ρ = −0.24 price vs rating; χ² = 15.8 offers vs rating band). Strength: broad BI tooling. Limitation: no predictive evaluation."]],
      [2.7*cm, 2.5*cm, 2.7*cm, 2.1*cm, 2.3*cm, W-12.3*cm])
B(["<b>All three comparators use secondary datasets</b> — Zomato extracts or a compiled "
   "delivery dataset. This study is built on primary data collected first-hand, which is "
   "what makes the locality-level analysis possible.",
   "<b>None of the three examines discount depth against rating</b>, which is the finding "
   "reported in Section 6 and the contribution absent from the prior work reviewed."])

# ---------------------------------------------------------------- 6
H("6. Results, insights, and recommendations")
table([["Metric", "Value", "Metric", "Value"],
       ["Unique restaurants", "1,686", "Rating model — RF test R²", "0.487"],
       ["Cities / localities", "7 / 70", "High-rating classifier ROC-AUC", "0.726"],
       ["Median cost for two", "₹300", "Delivery model — GB test R²", "0.651 (MAE 3.94 min)"],
       ["Median delivery time", "27 min", "Minutes per extra km", "3.43"],
       ["Restaurants with an offer", "94.1%", "K-Means silhouette (k = 4)", "0.215"]],
      [4.0*cm, 3.0*cm, 5.4*cm, W-12.4*cm])
h("Insight 1 — Deep discounting travels with lower ratings, not higher")
P("""Restaurants discounting 50% or more average <b>4.23</b> against <b>4.39</b> for everyone
else — 0.16 stars on a scale whose interquartile range is about 0.3 (Welch t = −13.3,
p &lt; 0.001). Offer depth is also the highest-ranked feature in the Random Forest, and χ²
confirms offer prevalence and rating band are not independent. <b>This is association, not
proven causation</b>, and the likelier direction is that struggling restaurants discount to
buy volume — but either way, discount depth reads as a distress signal, not a quality one.""")
h("Insight 2 — Price and rating are inversely related")
P("""Spearman ρ = −0.24; budget restaurants average 4.41 against 4.31 for premium, and
controlling for everything else a one-log-unit rise in cost costs 0.114 rating points.
Premium positioning carries a heavier burden of proof on a delivery platform than in a
dine-in setting.""")
h("Insight 3 — Delivery is a network problem, not a kitchen problem")
P("""Distance dominates the delivery model at <b>3.43 minutes per kilometre</b>, and city
effects are large and independent of it — Pune is about 10 minutes faster than Kolkata at
equal distance. That points at fleet density and city operations, not restaurant preparation.""")
h("Insight 4 — Rating is only half-explainable from listing data")
P("""The best rating model reaches R² 0.487 while the delivery model reaches 0.651 on the
same fields. Roughly half of rating variance lives in food quality, packaging and service
consistency that no listing attribute captures.""")
h("Recommendations")
B(["<b>Platform — treat discount depth as a risk indicator.</b> Route restaurants sustaining "
   "≥50% discounts into quality review rather than further promotional subsidy; the "
   "554-strong Value-laggard segment is the target list.",
   "<b>Platform — deploy the class-weighted classifier.</b> At 59% minority recall it finds "
   "more than four times as many under-performing restaurants as the unweighted model at "
   "identical ROC-AUC.",
   "<b>Platform — attack delivery through network design.</b> At 3.43 min/km, shrinking the "
   "median last mile beats any restaurant-side intervention; prioritise Kolkata, Hyderabad "
   "and Bengaluru, which sit 4–7 minutes above Pune.",
   "<b>Platform — stop ranking on listing metadata alone</b> (R² 0.487); feed order-level "
   "outcomes such as cancellations, complaints and reorder rate into any quality score.",
   "<b>Partners — do not buy rating with discounts.</b> Value performers reach 4.55 on ₹200 "
   "with 15% average depth; Value laggards spend 63% to reach 4.19.",
   "<b>Partners — fix speed before menu breadth.</b> Each minute of promised delivery costs "
   "0.008 rating points and each extra cuisine tag 0.012 — breadth reads as lack of focus."])

# ---------------------------------------------------------------- 7
H("7. Conclusion and references")
P("""This study built a primary dataset of 1,686 restaurants across 70 localities and seven
Indian metros by scraping Swiggy's public listing endpoint, then modelled rating and delivery
time, benchmarked fifteen brands and segmented the market on price, quality and speed. The
central outcome is that <b>the two questions a delivery business cares about are not equally
answerable from public data</b>: delivery time is well explained (R² 0.651, MAE under four
minutes) and reduces to network design at 3.43 min/km, while rating is only half explained
(R² 0.487) because the half that matters lives in food and service quality that listings do
not expose. The most commercially significant finding is that <b>promotional depth is
negatively associated with rating</b> — 0.16 stars lower for restaurants discounting 50% or
more — and that offer depth outranks price as a predictor. None of the three comparator
studies examines this relationship.""")
h("Limitations and future work")
P("""A single-day cross-section cannot separate cause from effect; promised rather than actual
delivery times are observed; traffic, weather and menu data are unavailable; the silhouette of
0.215 means the segments describe a continuum rather than natural kinds; and the endpoint
returns roughly 28 restaurants per locality in Swiggy's own ranking order, so the sample skews
toward restaurants the platform already promotes. Repeated collection over several weeks would
turn this cross-section into a panel and allow the discount–rating question to be tested
causally — observing whether ratings fall after discounts deepen, or the reverse.""")
h("References")
refs = [
 "Garg, A., Ayaan, M., Parekh, S. and Udandarao, V. (2025) <i>Food Delivery Time Prediction in Indian Cities Using Machine Learning Models.</i> arXiv:2503.15177. Available at: https://arxiv.org/abs/2503.15177",
 "Turai, S., Praneetha, P., Aishwarya, R. B., Adil, M. and Vangala, M. C. (2025) 'Analysis of restaurant ratings and reviews using machine learning', <i>World Journal of Advanced Research and Reviews</i>, 25(02), pp. 1039–1046. doi: 10.30574/wjarr.2025.25.2.0378",
 "Raj, H., Paul, S. and Kumar, K. (2025) 'A Comprehensive Analysis on Online Food Delivery: Taste The Change', <i>International Journal of Research Publication and Reviews</i>, 6(5), pp. 5962–5970.",
 "Swiggy (2026) <i>Restaurant listing endpoint.</i> Available at: https://www.swiggy.com/restaurants (Accessed: 19 September 2026).",
 "Pedregosa, F. et al. (2011) 'Scikit-learn: Machine Learning in Python', <i>Journal of Machine Learning Research</i>, 12, pp. 2825–2830.",
 "Seabold, S. and Perktold, J. (2010) 'statsmodels: Econometric and statistical modeling with Python', <i>Proceedings of the 9th Python in Science Conference</i>.",
]
for i, r in enumerate(refs, 1):
    flow.append(Paragraph(f"[{i}]&nbsp;&nbsp;{r}", SMALL)); S(2)

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
