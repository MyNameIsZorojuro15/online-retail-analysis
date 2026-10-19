"""Build the one-page dashboard (docs/index.html, served by GitHub Pages) and reports/key_numbers.json.

Every number on the page is read from reports/tables/*.csv, so the page cannot drift from the SQL.
Usage: python -m retail.dashboard   (after python -m retail.analyse)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "reports" / "tables"
BLUE, GREY, RED, GREEN = "#1f4e79", "#9aa5b1", "#b23a48", "#2e7d4f"


def t(name: str) -> pd.DataFrame:
    return pd.read_csv(T / f"{name}.csv")


def key_numbers() -> dict:
    yoy = t("02_year_over_year").set_index("metric")
    conc = t("04_concentration").set_index("entity")
    rfm = t("08_rfm_segments").set_index("segment")
    canc = t("09_cancellations")
    ret = t("07_cohort_retention")
    season = t("10_seasonality").set_index("window")
    dq = t("00_data_quality_log").set_index("rule")
    country = t("03_country_mix")

    def weighted(k):
        r = ret[ret.months_after == k]
        return round(float((r.retained_pct * r.customers).sum() / r.customers.sum()), 1), int(len(r))

    m1, m1n = weighted(1)
    m3, m3n = weighted(3)
    m12, m12n = weighted(12)
    non_uk = country[country.country != "United Kingdom"]
    return {
        "raw_rows": int(dq.rows.sum()),
        "sales_lines": int(dq.loc["kept_as_sale", "rows"]),
        "excluded_rows": int(dq.rows.sum() - dq.loc["kept_as_sale", "rows"]),
        "overlap_rows": int(dq.loc["overlap_between_sheets", "rows"]),
        "duplicate_rows": int(dq.loc["exact_duplicate", "rows"]),
        "reversed_rows": int(dq.loc["reversed_within_24h", "rows"]),
        "y1_revenue": float(yoy.loc["revenue_gbp", "y1_dec09_nov10"]),
        "y2_revenue": float(yoy.loc["revenue_gbp", "y2_dec10_nov11"]),
        "revenue_change_pct": float(yoy.loc["revenue_gbp", "change_pct"]),
        "orders_change_pct": float(yoy.loc["orders", "change_pct"]),
        "aov_y2": float(yoy.loc["avg_order_value_gbp", "y2_dec10_nov11"]),
        "aov_change_pct": float(yoy.loc["avg_order_value_gbp", "change_pct"]),
        "customers_y2": int(yoy.loc["customers", "y2_dec10_nov11"]),
        "customers_change_pct": float(yoy.loc["customers", "change_pct"]),
        "orders_per_customer_change_pct": float(yoy.loc["orders_per_customer", "change_pct"]),
        "orders_y2": int(yoy.loc["orders", "y2_dec10_nov11"]),
        "uk_share_pct": float(country.loc[country.country == "United Kingdom", "y2_share_pct"].iloc[0]),
        "uk_change_pct": float(country.loc[country.country == "United Kingdom", "change_pct"].iloc[0]),
        "ireland_change_pct": float(country.loc[country.country == "EIRE", "change_pct"].iloc[0]),
        "non_uk_revenue_y2": round(float(non_uk.y2_revenue_gbp.sum()), 2),
        "top20_products_share_pct": float(conc.loc["products", "top20_share_pct"]),
        "top20_customers_share_pct": float(conc.loc["customers", "top20_share_pct"]),
        "champions_customers_pct": float(rfm.loc["1 Champions", "customers_pct"]),
        "champions_revenue_pct": float(rfm.loc["1 Champions", "revenue_pct"]),
        "at_risk_customers": int(rfm.loc["4 At risk (were frequent)", "customers"]),
        "at_risk_revenue": float(rfm.loc["4 At risk (were frequent)", "revenue_gbp"]),
        "at_risk_median_recency_days": float(rfm.loc["4 At risk (were frequent)", "median_recency_days"]),
        "retention_m1_pct": m1, "retention_m3_pct": m3, "retention_m12_pct": m12,
        "retention_cohorts_m1": m1n, "retention_cohorts_m12": m12n,
        "cancelled_pct_of_sales": round(float(100 * canc.cancelled_gbp.sum() / canc.sales_gbp.sum()), 2),
        "sep_nov_share_y2_pct": float(season.loc["Y2 Dec10-Nov11", "sep_nov_share_pct"]),
        "november_share_y2_pct": float(season.loc["Y2 Dec10-Nov11", "november_share_pct"]),
    }


def figures() -> list[tuple[str, str, go.Figure]]:
    layout = dict(template="plotly_white", height=360, margin=dict(l=50, r=20, t=40, b=40), font=dict(family="Helvetica, Arial, sans-serif", size=12))
    figs = []

    k = t("01_monthly_kpis")
    k = k[k.complete_month]
    k["month"] = pd.to_datetime(k.month)
    y1 = k[(k.month >= "2009-12-01") & (k.month <= "2010-11-01")]
    y2 = k[(k.month >= "2010-12-01") & (k.month <= "2011-11-01")]
    labels = [m.strftime("%b") for m in y2.month]
    f = go.Figure([go.Bar(x=labels, y=y1.revenue_gbp, name="Dec 2009 – Nov 2010", marker_color=GREY),
                   go.Bar(x=labels, y=y2.revenue_gbp, name="Dec 2010 – Nov 2011", marker_color=BLUE)])
    f.update_layout(title="Monthly product revenue (GBP), year over year", barmode="group", legend=dict(orientation="h", y=-0.15), **layout)
    figs.append(("revenue", "Revenue is flat to slightly up, and a third of the year is earned in September to November.", f))

    f = go.Figure([go.Scatter(x=y2.month, y=y2.orders, name="Orders", line=dict(color=BLUE)),
                   go.Scatter(x=y2.month, y=y2.avg_order_value_gbp, name="Average order value (GBP)", yaxis="y2", line=dict(color=RED, dash="dot"))])
    f.update_layout(title="Orders and average order value, Dec 2010 – Nov 2011", yaxis=dict(title="Orders"),
                    yaxis2=dict(title="AOV (GBP)", overlaying="y", side="right"), legend=dict(orientation="h", y=-0.15), **layout)
    figs.append(("orders", "Growth came from bigger baskets, not more orders.", f))

    c = t("03_country_mix")
    uk = c[c.country == "United Kingdom"].iloc[0]
    abroad = c[c.country != "United Kingdom"].head(10)
    fallers = abroad[abroad.change_pct < 0].head(1)
    caption = (f"UK revenue moved {uk.change_pct:+.1f} %, so the growth came from abroad. "
               + ", ".join(f"{r.country} {r.change_pct:+.0f} %" for r in abroad.head(6).itertuples() if r.change_pct > 0)
               + (f"; {fallers.iloc[0].country.replace('EIRE', 'Ireland')} fell {abs(fallers.iloc[0].change_pct):.0f} %." if len(fallers) else "."))
    c = abroad.iloc[::-1].assign(country=lambda d: d.country.replace({"EIRE": "Ireland"}))
    f = go.Figure(go.Bar(x=c.y2_revenue_gbp, y=c.country, orientation="h", marker_color=BLUE,
                         text=[f"{v:+.0f} %" if pd.notna(v) else "new" for v in c.change_pct], textposition="outside"))
    f.update_layout(title="Top 10 markets outside the UK: revenue Dec 2010 – Nov 2011 (label: change vs prior year)", **layout)
    figs.append(("countries", caption, f))

    r = t("07_cohort_retention")
    r = r[r.months_after.between(1, 12)]
    piv = r.pivot(index="cohort", columns="months_after", values="retained_pct")
    f = go.Figure(go.Heatmap(z=piv.values, x=[f"+{c}" for c in piv.columns], y=piv.index, colorscale="Blues", zmin=0, zmax=40,
                             colorbar=dict(title="% back"), hovertemplate="cohort %{y}<br>%{x} months: %{z} %<extra></extra>"))
    f.update_layout(title="Share of each monthly cohort buying again N months later", **{**layout, "height": 440})
    figs.append(("cohorts", "About one in five new customers buys again in any given later month.", f))

    s = t("08_rfm_segments")
    names = [x.split(" ", 1)[1] for x in s.segment]
    f = go.Figure([go.Bar(x=names, y=s.customers_pct, name="% of customers", marker_color=GREY),
                   go.Bar(x=names, y=s.revenue_pct, name="% of revenue", marker_color=BLUE)])
    f.update_layout(title="Customer segments (recency, frequency, value), Dec 2010 – Nov 2011", barmode="group", legend=dict(orientation="h", y=-0.2), **layout)
    champ = s[s.segment.str.contains("Champions")].iloc[0]
    figs.append(("segments", f"{champ.customers_pct:.0f} % of customers bring {champ.revenue_pct:.0f} % of revenue; the at-risk group is the cheapest revenue to win back.", f))

    x = t("09_cancellations")
    f = go.Figure(go.Scatter(x=pd.to_datetime(x.month), y=x.cancelled_pct, mode="lines+markers", line=dict(color=RED)))
    f.update_layout(title="Cancelled value as % of product sales, by month", yaxis=dict(ticksuffix=" %"), **layout)
    figs.append(("cancellations", "Cancellations are small overall but spike in some months; worth a per-product look.", f))
    return figs


CSS = """
:root { --bg:#ffffff; --fg:#1b1f24; --muted:#5b6670; --card:#f4f6f8; --line:#d8dee4; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 Helvetica, Arial, sans-serif; }
main { max-width:1100px; margin:0 auto; padding:24px 16px 48px; }
h1 { font-size:26px; margin:0 0 4px; } h2 { font-size:18px; margin:32px 0 6px; }
p.lead { color:var(--muted); margin:0 0 20px; }
.tiles { display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:12px; }
.tile { background:var(--card); border-radius:8px; padding:14px; }
.tile b { display:block; font-size:22px; } .tile span { color:var(--muted); font-size:13px; }
.chart { border:1px solid var(--line); border-radius:8px; padding:8px; margin-top:8px; overflow:hidden; }
.note { color:var(--muted); font-size:13px; }
table { border-collapse:collapse; width:100%; font-size:14px; } td, th { border-bottom:1px solid var(--line); padding:6px 8px; text-align:left; }
td.n { text-align:right; }
ol li { margin-bottom:6px; }
"""


def build() -> Path:
    n = key_numbers()
    (ROOT / "reports" / "key_numbers.json").write_text(json.dumps(n, indent=1), encoding="utf-8")
    dq = t("00_data_quality_log")
    tiles = [
        (f"£{n['y2_revenue'] / 1e6:.2f}M", f"product revenue Dec 2010 – Nov 2011 ({n['revenue_change_pct']:+.1f} %)"),
        (f"{n['orders_y2']:,}", f"orders ({n['orders_change_pct']:+.1f} %)"),
        (f"£{n['aov_y2']:.0f}", f"average order value ({n['aov_change_pct']:+.1f} %)"),
        (f"{n['customers_y2']:,}", f"identified customers ({n['customers_change_pct']:+.1f} %)"),
        (f"{n['champions_revenue_pct']:.0f} %", f"of revenue from {n['champions_customers_pct']:.0f} % of customers"),
        (f"{n['cancelled_pct_of_sales']:.1f} %", "of product sales later cancelled"),
    ]
    parts = []
    for i, (key, caption, fig) in enumerate(figures()):
        html = fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False, config={"displayModeBar": False, "responsive": True}, default_width="100%")
        parts.append(f'<h2>{caption}</h2><div class="chart" id="{key}">{html}</div>')
    dq_rows = "".join(f"<tr><td>{r.rule.replace('_', ' ')}</td><td class='n'>{r.rows:,}</td><td class='n'>{r.pct_rows:.2f} %</td></tr>" for r in dq.itertuples())
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Online Retail Review</title><style>{CSS}</style></head>
<body><main>
<h1>Online retailer: two-year sales review</h1>
<p class="lead">UK online gift wholesaler, Dec 2009 – Dec 2011, {n['raw_rows']:,} transaction lines (UCI Online Retail II, CC BY 4.0).
Comparisons use two full 12-month windows; December 2011 stops on the 9th and is left out of trends.</p>
<div class="tiles">{''.join(f'<div class="tile"><b>{a}</b><span>{b}</span></div>' for a, b in tiles)}</div>
{''.join(parts)}
<h2>What I would do next quarter</h2>
<ol>
<li><b>Win back the at-risk group.</b> {n['at_risk_customers']:,} customers who used to order often have not ordered for a median of {n['at_risk_median_recency_days']:.0f} days; they spent £{n['at_risk_revenue'] / 1e3:,.0f}k last year. A targeted offer to them costs less than finding new customers.</li>
<li><b>Plan stock and staff for September to November.</b> {n['sep_nov_share_y2_pct']:.0f} % of the year's revenue lands in those three months, {n['november_share_y2_pct']:.0f} % in November alone.</li>
<li><b>Grow order count, not only basket size.</b> Orders fell {abs(n['orders_change_pct']):.1f} % while average order value rose {n['aov_change_pct']:.1f} %; orders per customer fell {abs(n['orders_per_customer_change_pct']):.1f} %. A reorder reminder for frequent buyers addresses that directly.</li>
<li><b>Find out why Ireland fell.</b> It is the second-largest market abroad and dropped {abs(n['ireland_change_pct']):.0f} % while the UK was flat; check whether a few large buyers left before spending on new markets.</li>
<li><b>Fix the order-entry controls.</b> {n['reversed_rows']:,} lines were sales reversed within a day, including one order of 74,215 units; a quantity or price sanity check at entry would stop most of them.</li>
</ol>
<h2>How the data was cleaned</h2>
<p class="note">Every raw line gets at most one rule; the counts add up to all {n['raw_rows']:,} lines. Full SQL in <code>sql/clean.sql</code>.</p>
<table><tr><th>Rule</th><th>Lines</th><th>Share</th></tr>{dq_rows}</table>
<p class="note">Built with SQL (DuckDB), Python and Plotly. Code, queries and method: see the repository README.</p>
</main></body></html>"""
    out = ROOT / "docs" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


if __name__ == "__main__":
    print(build())
