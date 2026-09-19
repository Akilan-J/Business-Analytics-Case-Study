"""
Swiggy locality sweep scraper
-----------------------------
Collects restaurant listing data from Swiggy's publicly accessible listing
endpoint (the same endpoint the public website calls to render
https://www.swiggy.com/restaurants) across a stratified grid of locality
coordinates in seven Indian metros.

Source        : https://www.swiggy.com/dapi/restaurants/list/v5
Method        : HTTP GET per locality coordinate, polite delay between calls
Unit of record: one restaurant listing as shown to a customer at that locality
Output        : data/swiggy_raw.csv  (one row per restaurant per locality probe)

No login, no paywall, no personal data. Only publicly displayed business
listing attributes are stored.
"""

import csv
import json
import random
import shutil
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "swiggy_raw.csv"
URL = ("https://www.swiggy.com/dapi/restaurants/list/v5"
       "?lat={lat}&lng={lng}&page_type=DESKTOP_WEB_LISTING")

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "application/json",
    "Accept-Language": "en-GB,en;q=0.9",
}

# Stratified sample: 10 localities per city, spread across the urban area so
# the sample is not dominated by a single high-income catchment.
LOCALITIES = {
    "Chennai": [
        ("T. Nagar", 13.0418, 80.2341), ("Adyar", 13.0012, 80.2565),
        ("Anna Nagar", 13.0850, 80.2101), ("Velachery", 12.9756, 80.2207),
        ("Nungambakkam", 13.0569, 80.2425), ("Porur", 13.0359, 80.1567),
        ("Tambaram", 12.9249, 80.1000), ("Perambur", 13.1143, 80.2330),
        ("OMR Thoraipakkam", 12.9400, 80.2340), ("Mylapore", 13.0339, 80.2698),
    ],
    "Bengaluru": [
        ("Koramangala", 12.9352, 77.6245), ("Indiranagar", 12.9784, 77.6408),
        ("Whitefield", 12.9698, 77.7500), ("Jayanagar", 12.9250, 77.5938),
        ("HSR Layout", 12.9116, 77.6446), ("Marathahalli", 12.9591, 77.6974),
        ("Malleshwaram", 13.0035, 77.5647), ("Electronic City", 12.8452, 77.6602),
        ("Hebbal", 13.0358, 77.5970), ("BTM Layout", 12.9166, 77.6101),
    ],
    "Hyderabad": [
        ("Gachibowli", 17.4401, 78.3489), ("Banjara Hills", 17.4126, 78.4392),
        ("Madhapur", 17.4483, 78.3915), ("Kukatpally", 17.4849, 78.4138),
        ("Secunderabad", 17.4399, 78.4983), ("Ameerpet", 17.4374, 78.4487),
        ("Dilsukhnagar", 17.3687, 78.5247), ("Kondapur", 17.4615, 78.3639),
        ("Miyapur", 17.4968, 78.3577), ("Begumpet", 17.4435, 78.4645),
    ],
    "Mumbai": [
        ("Andheri West", 19.1364, 72.8296), ("Bandra West", 19.0596, 72.8295),
        ("Powai", 19.1176, 72.9060), ("Lower Parel", 18.9960, 72.8258),
        ("Borivali", 19.2307, 72.8567), ("Thane West", 19.2183, 72.9781),
        ("Chembur", 19.0522, 72.9005), ("Malad West", 19.1868, 72.8484),
        ("Dadar", 19.0178, 72.8478), ("Vashi", 19.0771, 72.9986),
    ],
    "Delhi": [
        ("Connaught Place", 28.6315, 77.2167), ("Saket", 28.5245, 77.2066),
        ("Rohini", 28.7495, 77.0565), ("Dwarka", 28.5921, 77.0460),
        ("Lajpat Nagar", 28.5677, 77.2433), ("Janakpuri", 28.6219, 77.0878),
        ("Karol Bagh", 28.6519, 77.1909), ("Vasant Kunj", 28.5200, 77.1591),
        ("Pitampura", 28.6942, 77.1317), ("Mayur Vihar", 28.6092, 77.2952),
    ],
    "Pune": [
        ("Koregaon Park", 18.5362, 73.8939), ("Hinjewadi", 18.5913, 73.7389),
        ("Kothrud", 18.5074, 73.8077), ("Viman Nagar", 18.5679, 73.9143),
        ("Baner", 18.5590, 73.7868), ("Hadapsar", 18.5089, 73.9260),
        ("Wakad", 18.5985, 73.7625), ("Kharadi", 18.5515, 73.9470),
        ("Camp", 18.5158, 73.8785), ("Aundh", 18.5590, 73.8077),
    ],
    "Kolkata": [
        ("Park Street", 22.5530, 88.3520), ("Salt Lake", 22.5800, 88.4200),
        ("New Town", 22.5800, 88.4600), ("Behala", 22.4989, 88.3180),
        ("Ballygunge", 22.5290, 88.3650), ("Howrah", 22.5958, 88.2636),
        ("Dumdum", 22.6420, 88.4220), ("Garia", 22.4650, 88.3900),
        ("Shyambazar", 22.5990, 88.3700), ("Tollygunge", 22.4950, 88.3450),
    ],
}

FIELDS = ["scrape_ts", "city", "probe_locality", "probe_lat", "probe_lng",
          "restaurant_id", "name", "locality", "area_name", "cost_for_two_raw",
          "cuisines", "avg_rating", "total_ratings_raw", "delivery_time_min",
          "last_mile_km", "is_open", "veg_only", "offer_header", "offer_subheader", "offer_tag",
          "chain_parent_id", "listing_url"]


def find_restaurant_blocks(node):
    """Swiggy nests restaurant arrays at varying depths; walk and collect all."""
    out = []
    if isinstance(node, dict):
        rs = node.get("restaurants")
        if isinstance(rs, list) and rs and isinstance(rs[0], dict) and "info" in rs[0]:
            out.extend(rs)
        for v in node.values():
            out.extend(find_restaurant_blocks(v))
    elif isinstance(node, list):
        for v in node:
            out.extend(find_restaurant_blocks(v))
    return out


# Some networks (corporate / campus Wi-Fi) run a TLS-inspecting proxy whose CA
# sits in the OS keychain but not in Python's certifi bundle, so urllib raises
# CERTIFICATE_VERIFY_FAILED while curl succeeds. We try urllib first and fall
# back to curl (which uses the system trust store) for the rest of the run.
_USE_CURL = False


def _via_urllib(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _via_curl(url):
    cmd = ["curl", "-s", "--max-time", "30", "--compressed"]
    for k, v in HEADERS.items():
        cmd += ["-H", f"{k}: {v}"]
    cmd.append(url)
    out = subprocess.run(cmd, capture_output=True, timeout=60).stdout
    if not out:
        raise urllib.error.URLError("empty response from curl")
    return json.loads(out.decode("utf-8"))


def fetch(lat, lng, retries=3):
    global _USE_CURL
    url = URL.format(lat=lat, lng=lng)
    for attempt in range(retries):
        try:
            return _via_curl(url) if _USE_CURL else _via_urllib(url)
        except urllib.error.URLError as e:
            if isinstance(getattr(e, "reason", None), ssl.SSLCertVerificationError) \
                    or "CERTIFICATE_VERIFY_FAILED" in str(e):
                if not _USE_CURL and shutil.which("curl"):
                    print("    TLS verify failed under urllib -> switching to curl",
                          flush=True)
                    _USE_CURL = True
                    continue
            print(f"    retry {attempt + 1}/{retries} after {type(e).__name__}", flush=True)
            time.sleep(4 * (attempt + 1))
        except (json.JSONDecodeError, TimeoutError, subprocess.TimeoutExpired) as e:
            print(f"    retry {attempt + 1}/{retries} after {type(e).__name__}", flush=True)
            time.sleep(4 * (attempt + 1))
    return None


def row_from(r, ts, city, loc, lat, lng):
    i = r.get("info", {})
    sla = i.get("sla", {}) or {}
    disc = i.get("aggregatedDiscountInfoV3", {}) or {}
    return {
        "scrape_ts": ts, "city": city, "probe_locality": loc,
        "probe_lat": lat, "probe_lng": lng,
        "restaurant_id": i.get("id"), "name": i.get("name"),
        "locality": i.get("locality"), "area_name": i.get("areaName"),
        "cost_for_two_raw": i.get("costForTwo"),
        "cuisines": "|".join(i.get("cuisines") or []),
        "avg_rating": i.get("avgRating"),
        "total_ratings_raw": i.get("totalRatingsString"),
        "delivery_time_min": sla.get("deliveryTime"),
        "last_mile_km": sla.get("lastMileTravel"),
        "is_open": i.get("isOpen"),
        "veg_only": i.get("veg", False),
        "offer_header": disc.get("header"),
        "offer_subheader": disc.get("subHeader"),
        "offer_tag": disc.get("discountTag"),
        "chain_parent_id": i.get("parentId"),
        "listing_url": (r.get("cta") or {}).get("link"),
    }


def main():
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    seen_probe, written, failed = set(), 0, []

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for city, points in LOCALITIES.items():
            for loc, lat, lng in points:
                data = fetch(lat, lng)
                if not data:
                    failed.append(f"{city}/{loc}")
                    print(f"  FAIL {city:11s} {loc}", flush=True)
                    continue
                blocks = find_restaurant_blocks(data.get("data", {}))
                n = 0
                for r in blocks:
                    rid = (r.get("info") or {}).get("id")
                    key = (loc, rid)
                    if not rid or key in seen_probe:
                        continue
                    seen_probe.add(key)
                    w.writerow(row_from(r, ts, city, loc, lat, lng))
                    n += 1
                written += n
                fh.flush()
                print(f"  {city:11s} {loc:22s} +{n:3d}  (total {written})", flush=True)
                time.sleep(random.uniform(1.2, 2.4))   # polite crawl delay

    print(f"\nDone. {written} rows -> {OUT}")
    if failed:
        print("Failed probes:", ", ".join(failed))


if __name__ == "__main__":
    sys.exit(main())
