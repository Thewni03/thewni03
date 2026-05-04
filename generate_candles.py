import urllib.request
import json
from datetime import datetime, timedelta, timezone

USERNAME = "Thewni03"

def fetch_contributions():
    url = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return data.get("contributions", [])
    except Exception as e:
        print(f"Warning: could not fetch contributions: {e}")
        return []

def group_into_weeks(contributions):
    """Group daily contributions into calendar weeks (Mon-Sun), ordered oldest to newest."""
    if not contributions:
        return [], []

    # Parse and sort by date ascending
    days = sorted(contributions, key=lambda d: d["date"])

    # Find the Monday of the first day's week
    first = datetime.strptime(days[0]["date"], "%Y-%m-%d")
    start = first - timedelta(days=first.weekday())  # go back to Monday

    last = datetime.strptime(days[-1]["date"], "%Y-%m-%d")

    weeks = []
    week_labels = []
    cursor = start
    while cursor <= last:
        week_end = cursor + timedelta(days=6)
        total = 0
        for d in days:
            date = datetime.strptime(d["date"], "%Y-%m-%d")
            if cursor <= date <= week_end:
                total += d.get("count", 0)
        weeks.append(total)
        week_labels.append(cursor.strftime("%b %d"))
        cursor += timedelta(weeks=1)

    return weeks, week_labels

def generate_svg(weeks, week_labels):
    # Take the last 8 weeks (about 2 months) for clean display
    weeks = weeks[-8:]
    week_labels = week_labels[-8:]

    W, H, pad, bw = 640, 220, 40, 40
    n = len(weeks)
    if n == 0:
        return "<svg viewBox='0 0 640 220' xmlns='http://www.w3.org/2000/svg'><text x='320' y='110' text-anchor='middle' fill='#FF6B9D' font-size='14' font-family='sans-serif'>No data yet</text></svg>"

    max_val = max(weeks) or 1
    avail_w = W - pad * 2
    step = avail_w / n

    inner = ""
    for i, (w, label) in enumerate(zip(weeks, week_labels)):
        x = pad + i * step + step / 2
        bar_h = max(4, (w / max_val) * (H - pad * 2 - 40))
        y = H - pad - bar_h - 20

        intensity = w / max_val
        if intensity == 0:    c = "#ffeef4"
        elif intensity < 0.25: c = "#ffd6e7"
        elif intensity < 0.5:  c = "#ffb6c1"
        elif intensity < 0.75: c = "#FF6B9D"
        else:                  c = "#d63d78"

        # candle body
        inner += f'<rect x="{x-bw/2:.1f}" y="{y:.1f}" width="{bw}" height="{bar_h:.1f}" rx="4" fill="{c}"/>'
        # wick
        inner += f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y-12:.1f}" stroke="#ffb6c1" stroke-width="1.5" stroke-linecap="round"/>'
        # flame
        inner += f'<ellipse cx="{x:.1f}" cy="{y-17:.1f}" rx="4" ry="5.5" fill="#FFD700" opacity="0.95"/>'
        inner += f'<ellipse cx="{x:.1f}" cy="{y-19:.1f}" rx="2" ry="3" fill="#fff" opacity="0.5"/>'
        # commit count above candle
        if w > 0:
            inner += f'<text x="{x:.1f}" y="{y-25:.1f}" text-anchor="middle" fill="#d63d78" font-size="11" font-weight="600" font-family="sans-serif">{w}</text>'
        # week label below
        inner += f'<text x="{x:.1f}" y="{H-pad+4:.1f}" text-anchor="middle" fill="#ffb6c1" font-size="10" font-family="sans-serif">{label}</text>'

    updated = datetime.now(timezone.utc).strftime("%b %d, %Y")
    inner += f'<text x="{W//2}" y="{H-4}" text-anchor="middle" fill="#ffc0d0" font-size="9" font-family="sans-serif">updated {updated} UTC</text>'

    return f'''<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" role="img">
<title>Thewni weekly commit candle chart</title>
<desc>Candle chart showing weekly GitHub commits ordered by date</desc>
{inner}
</svg>'''

def main():
    print("Fetching contributions...")
    contributions = fetch_contributions()
    print(f"Got {len(contributions)} days of data")

    weeks, labels = group_into_weeks(contributions)
    print(f"Grouped into {len(weeks)} weeks")
    if labels:
        print(f"Date range: {labels[0]} → {labels[-1]}")

    svg = generate_svg(weeks, labels)
    with open("candles.svg", "w") as f:
        f.write(svg)
    print("candles.svg written successfully!")

if __name__ == "__main__":
    main()
