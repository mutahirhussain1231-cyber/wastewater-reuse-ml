"""
app.py - the ReWater web app (Streamlit).

Run on your own computer:
    streamlit run app.py
Then your browser opens at http://localhost:8501

Design: a corporate water-sector website (white header with the CUST logo,
full-width banners, section bands, dark footer), modelled on engineering and
water-association sites. Tool pages keep high-performance HMI rules: live
values in blue, green/amber/red only for status, flat process diagrams.
"""
import base64
import json
import sys
from pathlib import Path

import altair as alt
import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from config import (CLEAN_DATA, FIGURES_DIR, LABELS, LIMITS, MODELS_DIR,  # noqa: E402
                    TABLES_DIR, TARGETS)
from features import LAG_FEATURES, add_recent_effluent  # noqa: E402  (also needed to load the models)
from artwork import aerial_plant, data_uri, icon_predict, icon_recover, icon_reuse  # noqa: E402

# ---------------------------------------------------------------------------
# Settings you may want to change
# ---------------------------------------------------------------------------
APP_NAME = "ReWater"
TAGLINE = "Wastewater reuse decision support"
SURVEY_URL = "https://forms.gle/REPLACE-WITH-YOUR-FORM-LINK"
CREDIT = ("Built by students of Bioinformatics and Biosciences, "
          "Capital University of Science and Technology")
LOGO = ROOT / "assets" / "cust_logo.png"
HERO_PHOTO = ROOT / "assets" / "hero.jpg"   # optional: put an HD campus or plant photo here
QUICK_INPUTS = ["Q-E", "DBO-E", "DQO-E", "SS-E", "DBO-D", "DQO-D"]
REUSE_LIMIT = {"DBO-S": 30, "SS-S": 30}          # non-food irrigation (US EPA 2012)

# Colours: CUST navy and red, white and light-grey sections, blue for live data
HEADER, NAVY, RED, DEEP = "#1E2770", "#29337F", "#ED1E24", "#11163F"
CANVAS, PANEL, BORDER, BAND = "#FFFFFF", "#FFFFFF", "#DCE2EC", "#F3F6FA"
INK, MUTED, LIVE = "#1B2333", "#5B6577", "#2457C5"
TEAL = "#0E8C8C"
PASS, WARN, FAIL, GREY = "#2E8B57", "#B7791F", "#D7263D", "#A7B1C2"
SHORT = {"DBO-S": "BOD", "DQO-S": "COD", "SS-S": "TSS"}
FONT = "Inter, Segoe UI, Helvetica, Arial, sans-serif"

st.set_page_config(page_title=f"{APP_NAME} · {TAGLINE}", page_icon=str(LOGO), layout="wide")
LOGO64 = base64.b64encode(LOGO.read_bytes()).decode()
if HERO_PHOTO.exists():
    HERO_IMG = "data:image/jpeg;base64," + base64.b64encode(HERO_PHOTO.read_bytes()).decode()
else:
    HERO_IMG = data_uri(aerial_plant())
BANNER_IMG = data_uri(aerial_plant())


# ---------------------------------------------------------------------------
# Global style
# ---------------------------------------------------------------------------
def style():
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, .stApp, [class*="css"], .stMarkdown, button, input, label, textarea, p, li, td, th {{
    font-family: 'Inter', 'Segoe UI', sans-serif; }}
.stApp {{ background: {CANVAS}; color: {INK}; }}
header[data-testid="stHeader"], div[data-testid="stToolbar"], div[data-testid="stDecoration"] {{ display: none; }}
section[data-testid="stMain"] {{ overflow-x: hidden; }}
.block-container {{ padding: 88px 2rem 0 2rem; max-width: 1240px; }}
p, li {{ font-size: 15px; line-height: 1.6; }}
h1 {{ font-size: 26px !important; font-weight: 700 !important; color: {INK}; margin: 0 !important; padding: 0 !important; }}
h2 {{ font-size: 19px !important; font-weight: 600 !important; color: {INK}; }}
h3 {{ font-size: 16px !important; font-weight: 600 !important; color: {INK}; }}
.stMarkdown a, .stMarkdown a:hover {{ text-decoration: none !important; }}
.stMarkdown a.more {{ color: {HEADER}; }}
.bleed {{ width: 100vw; position: relative; left: 50%; margin-left: -50vw; }}
.wrap {{ max-width: 1240px; margin: 0 auto; padding: 0 2rem; }}

/* Header: navy utility strip + white bar */
.st-key-topbar {{ position: fixed; top: 0; left: 0; right: 0; z-index: 999; background: #fff; gap: 0 !important;
    height: 104px; box-sizing: border-box; padding-top: 32px !important; justify-content: flex-start;
    padding: 0 max(2.5rem, calc((100vw - 1240px) / 2 + 2rem)); box-shadow: 0 1px 0 {BORDER}, 0 6px 18px rgba(17,22,63,0.06); }}
.utility {{ position: fixed; top: 0; left: 0; right: 0; background: {HEADER}; color: #C9D1F2; font-size: 12.5px;
    padding: 0 max(2.5rem, calc((100vw - 1240px) / 2 + 2rem)); height: 32px; align-items: center;
    display: flex; justify-content: space-between; gap: 1rem; }}
.utility b {{ color: #fff; font-weight: 600; }}
.st-key-topbar [data-testid="stHorizontalBlock"] {{ align-items: center; gap: 0.3rem; padding: 0; }}
.st-key-topbar > div:last-child {{ height: 72px; display: flex; align-items: center; }}
.st-key-topbar > div:last-child > * {{ width: 100%; }}
.brand {{ display: flex; align-items: center; gap: 0.75rem; white-space: nowrap; }}
.brand img {{ width: 54px; height: 54px; }}
.brand .name {{ color: {HEADER}; font-size: 23px; font-weight: 800; line-height: 1.05; letter-spacing: -0.01em; }}
.brand .name span {{ color: {RED}; }}
.brand .tag {{ color: {MUTED}; font-size: 12.5px; font-weight: 500; }}
.st-key-topbar div[data-testid="stPageLink"] a {{ padding: 0.45rem 0.1rem; border-radius: 0; background: transparent; }}
.st-key-topbar div[data-testid="stPageLink"] a p {{ color: {INK}; font-size: 15px; font-weight: 500; }}
.st-key-topbar div[data-testid="stPageLink"] a:hover {{ background: transparent; }}
.st-key-topbar div[data-testid="stPageLink"] a:hover p {{ color: {RED}; }}
.nav-active {{ color: {HEADER}; font-size: 15px; font-weight: 700; padding: 0.45rem 0.1rem 0.2rem 0.1rem;
    border-bottom: 3px solid {RED}; display: inline-block; }}
.st-key-topbar [data-testid="stColumn"]:last-child {{ text-align: right; }}
.st-key-topbar [data-testid="stColumn"]:last-child div[data-testid="stPageLink"] a,
.nav-cta {{ white-space: nowrap; background: {RED}; border-radius: 6px; padding: 0.55rem 1.05rem; display: inline-block; }}
.st-key-topbar [data-testid="stColumn"]:last-child div[data-testid="stPageLink"] a p,
.nav-cta {{ color: #fff !important; font-weight: 600; font-size: 14.5px; }}
.st-key-topbar [data-testid="stColumn"]:last-child div[data-testid="stPageLink"] a:hover {{ background: #C8141A; }}
.st-key-topbar [data-testid="stColumn"]:last-child div[data-testid="stPageLink"] a:hover p {{ color: #fff !important; }}

/* Page banner (inner pages) */
.banner {{ min-height: 250px; display: flex; align-items: flex-end; background: {DEEP} center / cover no-repeat;
    margin-top: -1rem; }}
.banner .shade {{ width: 100%; background: linear-gradient(90deg, rgba(14,18,58,0.95) 0%, rgba(14,18,58,0.86) 45%,
    rgba(14,18,58,0.40) 100%); min-height: 250px; display: flex; align-items: flex-end; }}
.banner .wrap {{ width: 100%; padding-bottom: 2.1rem; }}
.crumb {{ color: #AEB8E6; font-size: 13px; margin-bottom: 0.7rem; }}
.crumb a {{ color: #DCE2F7; }} .crumb a:hover {{ color: #fff; }}
.crumb b {{ color: #fff; font-weight: 600; }}
.banner h1 {{ color: #fff !important; font-size: 40px !important; letter-spacing: -0.015em; }}
.banner h1:before {{ content: ""; display: block; width: 44px; height: 4px; background: {RED}; margin-bottom: 0.9rem; border-radius: 2px; }}
.banner .lead {{ color: #DCE2F7; font-size: 17px; line-height: 1.6; max-width: 72ch; margin: 0.6rem 0 0 0; }}
.page-gap {{ height: 1.2rem; }}

/* Home page */
.hero {{ background: {DEEP} center / cover no-repeat; margin-top: -1rem; }}
.hero .shade {{ background: linear-gradient(90deg, rgba(14,18,58,0.96) 0%, rgba(14,18,58,0.86) 42%, rgba(14,18,58,0.30) 100%);
    min-height: 540px; display: flex; align-items: center; }}
.hero .wrap {{ width: 100%; }}
.kicker {{ display: flex; align-items: center; gap: 0.7rem; font-size: 13px; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: #AEB8E6; }}
.kicker:before {{ content: ""; width: 36px; height: 3px; background: {RED}; border-radius: 2px; }}
.hero h1 {{ color: #fff !important; font-size: 54px !important; line-height: 1.08 !important; margin: 1.1rem 0 1.1rem 0 !important;
    max-width: 15ch; letter-spacing: -0.02em; }}
.hero h1 b {{ color: #7FD3E8; font-weight: 800; }}
.hero .lead {{ color: #DCE2F7; font-size: 18px; line-height: 1.6; max-width: 56ch; margin: 0 0 1.8rem 0; }}
.btn {{ display: inline-block; padding: 0.8rem 1.4rem; border-radius: 6px; font-weight: 600; font-size: 15px; margin: 0 0.6rem 0.6rem 0; }}
.btn-red {{ background: {RED}; color: #fff !important; }} .btn-red:hover {{ background: #C8141A; }}
.btn-line {{ border: 1.5px solid #fff; color: #fff !important; }} .btn-line:hover {{ background: #fff; color: {HEADER} !important; }}
.btn-navy {{ background: {HEADER}; color: #fff !important; }} .btn-navy:hover {{ background: {NAVY}; }}
.band {{ padding: 4.2rem 0; }} .band.grey {{ background: {BAND}; }} .band.white {{ background: #fff; }}
.band.navy {{ background: {HEADER}; color: #fff; }}
.eyebrow {{ color: {RED}; font-size: 13px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.6rem; }}
.h2 {{ font-size: 34px; font-weight: 700; color: {INK}; line-height: 1.2; letter-spacing: -0.015em; margin: 0 0 0.9rem 0; }}
.h2.light {{ color: #fff; }}
.sub {{ color: {MUTED}; font-size: 16.5px; line-height: 1.65; max-width: 70ch; margin: 0 0 2.2rem 0; }}
.intro {{ display: grid; grid-template-columns: 1fr 1.25fr; gap: 3.5rem; align-items: start; }}
.intro p {{ font-size: 17px; color: #3A4458; line-height: 1.7; margin: 0 0 1rem 0; }}
.more {{ color: {HEADER}; font-weight: 700; font-size: 15px; border-bottom: 2px solid {RED}; padding-bottom: 2px; }}
.more:hover {{ color: {RED}; }}
.cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.6rem; }}
.card {{ background: #fff; border: 1px solid {BORDER}; border-radius: 10px; overflow: hidden; display: flex; flex-direction: column;
    box-shadow: 0 2px 10px rgba(17,22,63,0.05); }}
.card:hover {{ box-shadow: 0 10px 26px rgba(17,22,63,0.12); border-color: #C3CBDA; }}
.card img {{ width: 100%; height: 170px; object-fit: cover; display: block; }}
.card .body {{ padding: 1.3rem 1.4rem 1.5rem 1.4rem; display: flex; flex-direction: column; flex: 1; }}
.card .tagline {{ color: {MUTED}; font-size: 12.5px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }}
.card h4 {{ font-size: 20px; color: {INK}; margin: 0.35rem 0 0.5rem 0; padding: 0; font-weight: 700; }}
.card p {{ color: {MUTED}; font-size: 15px; line-height: 1.6; flex: 1; margin: 0 0 1.1rem 0; }}
.stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; }}
.stat {{ padding: 0.4rem 1.6rem; border-left: 1px solid rgba(255,255,255,0.18); }}
.stat:first-child {{ border-left: none; padding-left: 0; }}
.stat .num {{ font-size: 46px; font-weight: 800; color: #fff; line-height: 1.05; font-variant-numeric: tabular-nums; }}
.stat .num span {{ color: #7FD3E8; }}
.stat .cap {{ color: #C9D1F2; font-size: 14.5px; margin-top: 0.4rem; line-height: 1.5; }}
.steps {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 2.2rem; }}
.step .no {{ width: 46px; height: 46px; border-radius: 50%; background: {HEADER}; color: #fff; font-weight: 700; font-size: 18px;
    display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; }}
.step h4 {{ font-size: 19px; color: {INK}; margin: 0 0 0.4rem 0; padding: 0; font-weight: 700; }}
.step p {{ color: {MUTED}; font-size: 15px; line-height: 1.6; margin: 0; }}
.cta {{ display: flex; justify-content: space-between; align-items: center; gap: 2rem; }}
.cta p {{ color: #C9D1F2; font-size: 16.5px; margin: 0; max-width: 60ch; }}

/* Footer */
.site-footer {{ background: {DEEP}; color: #AEB8E6; margin-top: 3.5rem; }}
.site-footer.flush {{ margin-top: 0; }}
.site-footer .cols {{ display: grid; grid-template-columns: 1.6fr 1fr 1fr 1.3fr; gap: 2.5rem; padding: 3.4rem 0 2.4rem 0; }}
.site-footer h5 {{ color: #fff; font-size: 14px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; margin: 0 0 1rem 0; padding: 0; }}
.site-footer a {{ display: block; color: #C9D1F2; font-size: 14.5px; margin-bottom: 0.55rem; }}
.site-footer a:hover {{ color: #fff; }}
.site-footer .small {{ font-size: 14px; line-height: 1.6; color: #AEB8E6; margin: 0 0 0.5rem 0; }}
.fbrand {{ display: flex; gap: 0.8rem; align-items: center; margin-bottom: 1rem; }}
.fbrand img {{ width: 52px; height: 52px; background: #fff; border-radius: 50%; padding: 3px; }}
.fbrand div {{ color: #fff; font-size: 22px; font-weight: 800; }}
.site-footer .bottom {{ border-top: 1px solid rgba(255,255,255,0.12); padding: 1.1rem 0 1.4rem 0; display: flex;
    justify-content: space-between; gap: 1rem; font-size: 13px; }}
.site-footer .bottom b {{ color: #fff; font-weight: 600; }}

@media (max-width: 900px) {{
  .st-key-topbar {{ position: relative; padding: 0 1rem; }}
  .st-key-topbar [data-testid="stHorizontalBlock"] {{ height: auto; padding: 0.7rem 0; }}
  .st-key-topbar {{ height: auto; padding-top: 0 !important; width: 100vw !important; max-width: 100vw !important; left: 50%; margin-left: -50vw !important; }}
  .st-key-topbar > div:last-child {{ height: auto; }}
  .utility {{ position: static; height: auto; padding: 0.4rem 1rem !important; }}
  .utility {{ margin: 0 -1rem; padding: 0.4rem 1rem; flex-direction: column; gap: 0.1rem; }}
  .st-key-topbar [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; column-gap: 1.1rem; row-gap: 0.2rem; }}
  .st-key-topbar [data-testid="stColumn"] {{ width: auto !important; flex: 0 0 auto !important; min-width: 0 !important; }}
  .st-key-topbar [data-testid="stColumn"]:first-child {{ width: 100% !important; flex: 0 0 100% !important; margin-bottom: 0.3rem; }}
  .block-container {{ padding: 0 1rem; }}
  .wrap {{ padding: 0 1rem; }}
  .hero h1 {{ font-size: 36px !important; }} .hero .shade {{ min-height: 520px; }}
  .banner h1 {{ font-size: 30px !important; }}
  .intro, .cards, .steps, .site-footer .cols {{ grid-template-columns: 1fr; gap: 1.6rem; }}
  .stats {{ grid-template-columns: 1fr 1fr; row-gap: 1.6rem; }}
  .stat {{ border-left: none; padding-left: 0; }}
  .cta, .site-footer .bottom {{ flex-direction: column; align-items: flex-start; }}
  .band {{ padding: 3rem 0; }} .h2 {{ font-size: 27px; }}
  .kpi {{ margin-bottom: 0.6rem; }}
}}

/* Panels */
[class*="st-key-panel_"] {{ background: {PANEL}; border: 1px solid {BORDER} !important;
    border-radius: 10px; padding: 1.1rem 1.25rem 1.2rem 1.25rem !important; }}
[class*="st-key-panel_"] div[data-baseweb="input"] > div, [class*="st-key-panel_"] div[data-baseweb="select"] > div {{
    background: #F5F7FA; }}
.panel-title {{ font-size: 15px; font-weight: 600; color: {INK}; margin-bottom: 0.15rem; }}
.panel-sub {{ font-size: 13px; color: {MUTED}; margin-bottom: 0.6rem; }}

/* KPI tile with analog limit gauge */
.kpi {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 10px; padding: 1rem 1.1rem 0.9rem 1.1rem; height: 100%; }}
.kpi .label {{ font-size: 13px; color: {MUTED}; font-weight: 500; }}
.kpi .value {{ font-size: 30px; font-weight: 700; color: {LIVE}; margin: 0.2rem 0 0.55rem 0;
    font-variant-numeric: tabular-nums; }}
.kpi .value span {{ font-size: 14px; color: {MUTED}; font-weight: 500; margin-left: 0.25rem; }}
.gauge {{ position: relative; height: 8px; border-radius: 4px; background: #E3E8F0; overflow: visible; }}
.gauge .over {{ position: absolute; top: 0; bottom: 0; right: 0; background: #F6D5D9; border-radius: 0 4px 4px 0; }}
.gauge .mark {{ position: absolute; top: -4px; width: 3px; height: 16px; background: {INK}; border-radius: 2px; }}
.gauge .limit {{ position: absolute; top: -6px; width: 0; height: 20px; border-left: 2px dashed {FAIL}; }}
.kpi .foot {{ display: flex; justify-content: space-between; font-size: 12.5px; color: {MUTED}; margin-top: 0.55rem; }}
.status {{ font-weight: 600; }} .ok {{ color: {PASS}; }} .bad {{ color: {FAIL}; }} .warn {{ color: {WARN}; }}

/* Process diagram */
.flow {{ margin-bottom: 0.7rem; display: grid; grid-template-columns: 1fr 28px 1fr 28px 1fr 28px 1fr 28px 1fr; align-items: stretch; }}
.unit {{ border: 1.5px solid {NAVY}; border-radius: 8px; padding: 0.75rem 0.8rem; background: #F7F9FC; }}
.unit .n {{ font-size: 12px; color: {MUTED}; font-weight: 600; }}
.unit .t {{ font-size: 14.5px; font-weight: 600; color: {INK}; margin: 0.1rem 0 0.5rem 0; }}
.unit .r {{ display: flex; justify-content: space-between; font-size: 13px; color: {MUTED}; padding: 0.12rem 0; }}
.unit .r b {{ color: {LIVE}; font-weight: 600; font-variant-numeric: tabular-nums; }}
.unit.end {{ border-color: {PASS}; background: #EEF7F1; }}
.pipe {{ position: relative; }}
.pipe:before {{ content: ""; position: absolute; left: 3px; right: 9px; top: 50%; border-top: 2px solid {NAVY}; }}
.pipe:after {{ content: ""; position: absolute; right: 2px; top: calc(50% - 6px); border-left: 9px solid {NAVY};
    border-top: 6px solid transparent; border-bottom: 6px solid transparent; }}
@media (max-width: 900px) {{ .flow {{ grid-template-columns: 1fr; }} .pipe {{ height: 22px; }}
  .pipe:before {{ left: 50%; right: auto; top: 2px; bottom: 6px; border-top: none; border-left: 2px solid {NAVY}; }}
  .pipe:after {{ left: calc(50% - 5px); right: auto; top: auto; bottom: 0; border-left: 6px solid transparent;
    border-right: 6px solid transparent; border-top: 8px solid {NAVY}; border-bottom: none; }} }}

div[data-testid="stExpander"] details {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 10px; }}
div[data-testid="stExpander"] summary p {{ font-weight: 600; font-size: 14.5px; color: {INK}; }}

/* Tool cards */
.tool {{ font-size: 13.5px; color: {MUTED}; margin: 0.2rem 0 0.5rem 0; min-height: 3.2em; }}
div[data-testid="stPageLink"] a {{ border-radius: 8px; }}
.st-key-panel_tools div[data-testid="stPageLink"] a {{ border: 1px solid {NAVY}; padding: 0.35rem 0.8rem; }}
.st-key-panel_tools div[data-testid="stPageLink"] a p {{ color: {NAVY}; font-weight: 600; font-size: 14px; }}
.st-key-panel_tools div[data-testid="stPageLink"] a:hover {{ background: {NAVY}; }}
.st-key-panel_tools div[data-testid="stPageLink"] a:hover p {{ color: #fff; }}

/* Results */
.verdict {{ border-radius: 8px; padding: 0.8rem 1rem; margin: 0.4rem 0 0.6rem 0; border: 1px solid; font-size: 14.5px; }}
.v-pass {{ border-color: #9FD3B4; background: #EEF7F1; color: #1E5E3B; }}
.v-warn {{ border-color: #E7C98C; background: #FBF4E6; color: #6B4A10; }}
.v-fail {{ border-color: #F0A3AD; background: #FCEDEF; color: #7D1422; }}
div[data-testid="stMetric"] {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 10px; padding: 0.8rem 1rem; }}
div[data-testid="stMetricLabel"] p {{ font-size: 13px !important; color: {MUTED}; }}
div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * {{ color: {LIVE};
    font-family: 'Inter', 'Segoe UI', sans-serif; font-weight: 700; font-size: 28px; }}

/* Footer */
.footer {{ margin-top: 2.4rem; padding: 1rem 0 0.4rem 0; border-top: 1px solid {BORDER}; display: flex;
    gap: 0.8rem; align-items: center; color: {MUTED}; font-size: 13px; }}
.footer img {{ width: 34px; height: 34px; }} .footer b {{ color: {INK}; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)


def topbar(current_title: str):
    with st.container(key="topbar"):
        st.markdown('<div class="utility"><span><b>Capital University of Science and Technology</b> · '
                    'Department of Bioinformatics and Biosciences</span>'
                    '<span>Environmental Biotechnology · Wastewater in the circular economy</span></div>',
                    unsafe_allow_html=True)
        cols = st.columns([3.2, 0.62, 0.8, 0.66, 0.8, 0.86, 0.62, 1.25], vertical_alignment="center")
        cols[0].markdown(f'<div class="brand"><img src="data:image/png;base64,{LOGO64}" '
                         f'alt="CUST logo"><div><div class="name">Re<span>Water</span></div>'
                         f'<div class="tag">{TAGLINE}</div></div></div>', unsafe_allow_html=True)
        for col, (key, page) in zip(cols[1:], PAGES.items()):
            label = NAV_LABELS[key]
            if page.title == current_title:
                cls = "nav-cta" if key == "survey" else "nav-active"
                col.markdown(f'<span class="{cls}">{label}</span>', unsafe_allow_html=True)
            else:
                col.page_link(page, label=label)


def page_header(crumb: str, title: str, desc: str):
    """Full-width banner with breadcrumb, title and lead (WSP-style page header)."""
    st.markdown(f'<div class="bleed banner" style="background-image:url({BANNER_IMG})"><div class="shade"><div class="wrap">'
                f'<div class="crumb"><a href="./" target="_self">Home</a> &nbsp;›&nbsp; <b>{crumb}</b></div>'
                f'<h1>{title}</h1><p class="lead">{desc}</p></div></div></div><div class="page-gap"></div>',
                unsafe_allow_html=True)


def panel_title(title: str, sub: str = ""):
    st.markdown(f'<div class="panel-title">{title}</div>' + (f'<div class="panel-sub">{sub}</div>' if sub else ""),
                unsafe_allow_html=True)


def footer_html(flush: bool = False) -> str:
    link = lambda path, text: f'<a href="./{path}" target="_self">{text}</a>'  # noqa: E731
    return (f'<div class="bleed site-footer{" flush" if flush else ""}"><div class="wrap"><div class="cols">'
            f'<div><div class="fbrand"><img src="data:image/png;base64,{LOGO64}" alt="CUST logo"><div>ReWater</div></div>'
            f'<p class="small">An open tool for deciding when treated wastewater is fit for reuse, and what a '
            f'treatment plant could recover.</p><p class="small"><b style="color:#fff">{CREDIT}</b></p></div>'
            f'<div><h5>Tools</h5>{link("predictor", "Effluent predictor")}{link("reuse", "Reuse checker")}'
            f'{link("recovery", "Resource recovery")}</div>'
            f'<div><h5>Project</h5>{link("plant-data", "Plant data")}{link("model", "About the model")}'
            f'{link("survey", "Learn &amp; survey")}</div>'
            f'<div><h5>Data and standards</h5><p class="small">UCI Machine Learning Repository, Water Treatment Plant '
            f'dataset (CC BY 4.0)</p><p class="small">Pakistan EQS for municipal effluents · US EPA (2012) Guidelines '
            f'for Water Reuse · WHO (2006)</p></div></div>'
            f'<div class="bottom"><span>© 2026 ReWater · Open-source under the MIT licence</span>'
            f'<span>Capital University of Science and Technology, Islamabad</span></div></div></div>')


def footer():
    st.markdown(footer_html(), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Models and data (cached so they load only once)
# ---------------------------------------------------------------------------
@st.cache_resource
def load_models():
    meta_path = MODELS_DIR / "metadata.json"
    if not meta_path.exists():
        return None, None
    meta = json.loads(meta_path.read_text())
    models = {t: joblib.load(MODELS_DIR / f"model_{t}.joblib") for t in meta["targets"]}
    return meta, models


@st.cache_data
def load_data():
    if not CLEAN_DATA.exists():
        return None
    return pd.read_csv(CLEAN_DATA, parse_dates=["DATE"])


meta, models = load_models()
data = load_data()


def chart_style(chart, height=280):
    """Apply the app's style to an Altair chart."""
    return (chart.properties(height=height, background="transparent")
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#E6EBF2", domainColor=BORDER,
                            tickColor=BORDER, labelFont=FONT, titleFont=FONT, labelFontSize=12, titleFontSize=12,
                            titleFontWeight=500)
            .configure_legend(labelColor=MUTED, titleColor=MUTED, labelFont=FONT, titleFont=FONT, labelFontSize=12)
            .configure_title(color=INK, font=FONT, anchor="start"))


def check_limits(values: dict) -> pd.DataFrame:
    """values: {'DBO-S': .., 'DQO-S': .., 'SS-S': .., 'pH': ..} -> pass/fail table."""
    rows = []
    for standard, lim in LIMITS.items():
        verdicts, reasons = [], []
        for key, limit in lim.items():
            v = values.get(key)
            if v is None:
                continue
            if key == "pH":
                ok = limit[0] <= v <= limit[1]
                reasons.append(f"pH {v:.1f} ({'within' if ok else 'outside'} {limit[0]}–{limit[1]})")
            else:
                ok = v <= limit
                reasons.append(f"{TARGETS[key]} {v:.1f} vs ≤{limit}")
            verdicts.append(ok)
        if verdicts:
            rows.append({
                "Standard": standard,
                "Verdict": "✅ Meets" if all(verdicts) else "❌ Does not meet",
                "Details": "; ".join(reasons),
            })
    return pd.DataFrame(rows)


def verdict_box(table: pd.DataFrame) -> None:
    met = table.loc[table["Verdict"].str.startswith("✅"), "Standard"].tolist()
    if any("eaten raw" in s for s in met):
        cls, text = "v-pass", ("✔ <b>Fit even for food crops eaten raw</b> (by BOD, TSS and pH). "
                               "Pathogen tests (E. coli) are still required before real use.")
    elif any("non-food" in s for s in met):
        cls, text = "v-pass", ("✔ <b>Fit for irrigating non-food or processed crops, parks and landscaping.</b> "
                               "Needs further treatment before irrigating vegetables eaten raw.")
    elif any("inland" in s for s in met):
        cls, text = "v-warn", ("▲ <b>Can be discharged to rivers and streams, but not reused for irrigation</b> "
                               "without further treatment.")
    else:
        cls, text = "v-fail", "✖ <b>Does not meet discharge limits.</b> Further treatment is needed."
    st.markdown(f'<div class="verdict {cls}">{text}</div>', unsafe_allow_html=True)


def limits_chart(values: dict):
    """Bars of BOD/COD/TSS with a tick at each standard's limit (log scale)."""
    order = ["BOD", "COD", "TSS"]
    names = {"Discharge to inland waters": "Discharge to rivers",
             "Irrigation of non-food / processed crops": "Irrigation, non-food crops",
             "Irrigation of food crops eaten raw": "Irrigation, food crops eaten raw"}
    bars = pd.DataFrame([{"Parameter": SHORT[k], "mg/L": round(max(v, 1.0), 1)}
                         for k, v in values.items() if k in SHORT])
    ticks = pd.DataFrame([{"Parameter": SHORT[k], "Limit": lim[k], "Standard": names[s.split(" (")[0]]}
                          for s, lim in LIMITS.items() for k in SHORT if k in lim])
    x = alt.X("mg/L:Q", title="mg/L (log scale)",
              scale=alt.Scale(type="log", domain=[1, 300]), axis=alt.Axis(grid=False, values=[1, 3, 10, 30, 100, 300]))
    base = alt.Chart(bars).mark_bar(color=LIVE, cornerRadiusEnd=3, height=14).encode(
        y=alt.Y("Parameter:N", sort=order, title=None), x=x, x2=alt.datum(1),
        tooltip=["Parameter", "mg/L"])
    marks = alt.Chart(ticks).mark_tick(thickness=3, size=30).encode(
        y=alt.Y("Parameter:N", sort=order), x=alt.X("Limit:Q"),
        color=alt.Color("Standard:N", scale=alt.Scale(domain=list(names.values()), range=[GREY, WARN, FAIL]),
                        legend=alt.Legend(orient="bottom", title="Limit", labelLimit=260)),
        tooltip=["Standard", "Parameter", "Limit"])
    return chart_style(base + marks, height=165)


def kpi_tile(label: str, value: float, unit: str, limit: float, limit_name: str, span: float):
    """KPI with an analog gauge: value marker against the limit (ISA-101 style)."""
    pos = min(100, 100 * value / span)
    lim = min(100, 100 * limit / span)
    ok = value <= limit
    status = f'<span class="status {"ok" if ok else "bad"}">{"✔ Within limit" if ok else "✖ Above limit"}</span>'
    return (f'<div class="kpi"><div class="label">{label}</div>'
            f'<div class="value">{value:.0f}<span>{unit}</span></div>'
            f'<div class="gauge"><div class="over" style="left:{lim:.1f}%"></div>'
            f'<div class="limit" style="left:{lim:.1f}%"></div><div class="mark" style="left:calc({pos:.1f}% - 1px)"></div></div>'
            f'<div class="foot"><span>{limit_name}: {limit:g} {unit}</span>{status}</div></div>')


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def flow_html(med: dict) -> str:
    """Flat left-to-right diagram of the plant with typical values at each stage."""
    drop_bod = 100 * (1 - med["DBO-S"] / med["DBO-E"])
    units = [
        ("1", "Raw sewage inlet", [("Flow", f'{med["Q-E"]:,.0f} m³/d'), ("BOD", f'{med["DBO-E"]:.0f} mg/L'),
                                  ("COD", f'{med["DQO-E"]:.0f} mg/L'), ("TSS", f'{med["SS-E"]:.0f} mg/L')], ""),
        ("2", "Primary settler", [("BOD in", f'{med["DBO-P"]:.0f} mg/L'), ("TSS in", f'{med["SS-P"]:.0f} mg/L'),
                                 ("Settles", "solids, grit")], ""),
        ("3", "Biological treatment", [("BOD in", f'{med["DBO-D"]:.0f} mg/L'), ("COD in", f'{med["DQO-D"]:.0f} mg/L'),
                                      ("TSS in", f'{med["SS-D"]:.0f} mg/L')], ""),
        ("4", "Treated effluent", [("BOD", f'{med["DBO-S"]:.0f} mg/L'), ("COD", f'{med["DQO-S"]:.0f} mg/L'),
                                  ("TSS", f'{med["SS-S"]:.0f} mg/L')], ""),
        ("5", "Reuse or discharge", [("BOD removed", f"{drop_bod:.0f}%"), ("Typical use", "non-food crops"),
                                    ("Check", "pathogens")], " end"),
    ]
    cells = []
    for i, (n, t, rows, extra) in enumerate(units):
        body = "".join(f'<div class="r"><span>{k}</span><b>{v}</b></div>' for k, v in rows)
        cells.append(f'<div class="unit{extra}"><div class="n">Stage {n}</div><div class="t">{t}</div>{body}</div>')
        if i < len(units) - 1:
            cells.append('<div class="pipe"></div>')
    return f'<div class="flow">{"".join(cells)}</div>'


def plant_summary():
    med = {c: data[c].median() for c in data.columns if c != "DATE"}
    both = data[["DBO-S", "SS-S"]].dropna()
    ok_days = 100 * ((both["DBO-S"] <= REUSE_LIMIT["DBO-S"]) & (both["SS-S"] <= REUSE_LIMIT["SS-S"])).mean()
    return med, both, ok_days


def plant_snapshot():
    """KPI tiles, process diagram and recent trend (top of the Plant data page)."""
    med, both, ok_days = plant_summary()
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(kpi_tile("Treated water BOD (typical day)", med["DBO-S"], "mg/L", 30, "Irrigation limit", 60),
                unsafe_allow_html=True)
    k2.markdown(kpi_tile("Treated water COD (typical day)", med["DQO-S"], "mg/L", 150, "Discharge limit", 200),
                unsafe_allow_html=True)
    k3.markdown(kpi_tile("Treated water TSS (typical day)", med["SS-S"], "mg/L", 30, "Irrigation limit", 60),
                unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi"><div class="label">Days fit for non-food irrigation</div>'
                f'<div class="value">{ok_days:.0f}<span>% of {len(both)} days</span></div>'
                f'<div class="gauge"><div class="mark" style="left:calc({ok_days:.1f}% - 1px)"></div></div>'
                f'<div class="foot"><span>BOD and TSS ≤ 30 mg/L</span>'
                f'<span class="status warn">▲ {100 - ok_days:.0f}% need more</span></div></div>',
                unsafe_allow_html=True)
    st.write("")
    with st.container(border=True, key="panel_flow"):
        panel_title("Treatment process", "Typical (median) values at each sampling point, flowing left to right")
        st.markdown(flow_html(med), unsafe_allow_html=True)
        st.caption(f"Based on {len(data)} days of records ({data['DATE'].min():%b %Y}–{data['DATE'].max():%b %Y}). "
                   "BOD entering the primary settler is higher than at the inlet because of internal return flows.")
    with st.container(border=True, key="panel_trend"):
        panel_title("Treated-water trend", "Effluent BOD and TSS over the final 120 records, with the irrigation limit")
        recent = data.dropna(subset=["DBO-S"]).tail(120)
        long = recent[["DATE", "DBO-S", "SS-S"]].melt("DATE", var_name="code", value_name="mg/L").dropna()
        long["Parameter"] = long["code"].map(SHORT)
        lines = alt.Chart(long).mark_line(strokeWidth=1.8).encode(
            x=alt.X("DATE:T", title=None), y=alt.Y("mg/L:Q", title="mg/L"),
            color=alt.Color("Parameter:N", scale=alt.Scale(domain=["BOD", "TSS"], range=[LIVE, TEAL]),
                            legend=alt.Legend(orient="top-left", title=None)),
            tooltip=[alt.Tooltip("DATE:T", format="%d %b %Y"), "Parameter", alt.Tooltip("mg/L:Q", format=".0f")])
        rule = alt.Chart(pd.DataFrame({"y": [30]})).mark_rule(color=FAIL, strokeDash=[5, 4]).encode(y="y:Q")
        label = alt.Chart(pd.DataFrame({"y": [30], "t": ["Irrigation limit 30 mg/L"]})).mark_text(
            align="left", dx=4, dy=-7, color=FAIL, fontSize=11, font=FONT).encode(y="y:Q", text="t:N", x=alt.value(0))
        st.altair_chart(chart_style(lines + rule + label, height=250), theme=None, width="stretch")


def page_home():
    if data is None or meta is None:
        st.error("Run `python src/prepare_data.py` and `python src/train_models.py` first.")
        st.stop()
    med, both, ok_days = plant_summary()
    drop_bod = 100 * (1 - med["DBO-S"] / med["DBO-E"])
    n_models = 6

    def card(img, tag, title, text, path, more):
        return (f'<div class="card"><img src="{img}" alt=""><div class="body"><div class="tagline">{tag}</div>'
                f'<h4>{title}</h4><p>{text}</p><div><a class="more" href="./{path}" target="_self">{more} →</a></div>'
                f'</div></div>')

    def step(no, title, text):
        return f'<div class="step"><div class="no">{no}</div><h4>{title}</h4><p>{text}</p></div>'

    def stat(num, unit, cap):
        return f'<div class="stat"><div class="num">{num}<span>{unit}</span></div><div class="cap">{cap}</div></div>'

    html = (
        # Hero
        f'<div class="bleed hero" style="background-image:url({HERO_IMG})"><div class="shade"><div class="wrap">'
        f'<div class="kicker">Environmental Biotechnology · CUST</div>'
        f'<h1>Turning wastewater into a <b>resource</b></h1>'
        f'<p class="lead">ReWater uses machine learning on real treatment-plant records to predict treated-water '
        f'quality, check it against discharge and irrigation standards, and estimate the energy and nutrients a '
        f'plant could recover.</p>'
        f'<a class="btn btn-red" href="./predictor" target="_self">Predict effluent quality</a>'
        f'<a class="btn btn-line" href="./reuse" target="_self">Check a lab result</a>'
        f'</div></div></div>'
        # Intro
        f'<div class="bleed band white"><div class="wrap"><div class="intro">'
        f'<div><div class="eyebrow">Wastewater in the circular economy</div>'
        f'<div class="h2">Wastewater is not waste. It is water, energy and nutrients in the wrong place.</div></div>'
        f'<div><p>Pakistan treats only a small share of its wastewater while its water grows scarcer. A treatment '
        f'plant can do more than clean water: activated sludge and membranes make it safe to reuse, anaerobic '
        f'digestion turns organic matter into biogas, and nitrogen and phosphorus can return to farms as fertiliser.</p>'
        f'<p>ReWater brings these ideas together in one free, open tool, built on a literature review, a public '
        f'survey and machine-learning models trained on {len(data)} days of plant data.</p>'
        f'<a class="more" href="./survey" target="_self">Learn about reuse and its risks →</a></div>'
        f'</div></div></div>'
        # Tools
        f'<div class="bleed band grey"><div class="wrap">'
        f'<div class="eyebrow">Tools</div><div class="h2">What you can do with ReWater</div>'
        f'<p class="sub">Three tools for students, plant operators and planners. Each one runs in your browser '
        f'and explains its result in plain language.</p><div class="cards">'
        + card(icon_predict(), "Machine learning", "Effluent predictor",
               "Enter today's plant readings and get the expected BOD, COD and suspended solids of the treated water, "
               "with the typical error of each model.", "predictor", "Open the predictor")
        + card(icon_reuse(), "Standards", "Reuse checker",
               "Compare a lab result with Pakistan's discharge limits and US EPA irrigation guidelines to see which "
               "uses the water allows.", "reuse", "Check a result")
        + card(icon_recover(), "Circular economy", "Resource recovery",
               "Estimate the biogas, electricity, struvite fertiliser and bioplastic a plant of any size could "
               "recover each day.", "recovery", "Estimate recovery")
        + f'</div></div></div>'
        # Stats
        f'<div class="bleed band navy"><div class="wrap"><div class="stats">'
        + stat(f"{len(data)}", "", "days of real treatment-plant records used for training")
        + stat(f"{drop_bod:.0f}", "%", "of organic load (BOD) removed by the plant on a typical day")
        + stat(f"{ok_days:.0f}", "%", "of days the treated water met non-food irrigation limits")
        + stat(f"{n_models}", "", "models compared for each parameter, including two benchmarks")
        + f'</div></div></div>'
        # Steps
        f'<div class="bleed band white"><div class="wrap">'
        f'<div class="eyebrow">How it works</div><div class="h2">From plant readings to a reuse decision</div>'
        f'<p class="sub">The same three steps an operator follows, done in seconds.</p><div class="steps">'
        + step(1, "Enter readings", "Flow, BOD, COD and solids measured at the inlet and inside the plant, plus the "
                                    "latest effluent results.")
        + step(2, "Predict quality", "Models trained on historical records estimate tomorrow's treated-water quality "
                                     "before the lab result is back.")
        + step(3, "Check the limits", "The result is compared with discharge and irrigation standards, with a clear "
                                      "verdict on safe uses.")
        + f'</div></div></div>'
        # Process
        f'<div class="bleed band grey"><div class="wrap">'
        f'<div class="eyebrow">Inside the plant</div><div class="h2">How the studied plant treats its water</div>'
        f'<p class="sub">Typical (median) values at each sampling point of the plant behind our dataset.</p>'
        f'{flow_html(med)}<p style="margin-top:1.4rem"><a class="more" href="./plant-data" target="_self">'
        f'Explore the plant data →</a></p></div></div>'
        # Survey CTA
        f'<div class="bleed band navy"><div class="wrap"><div class="cta">'
        f'<div><div class="h2 light">Would you use recycled water?</div>'
        f'<p>Help our research: a 5-minute anonymous survey on how people in Pakistan feel about reusing treated '
        f'wastewater.</p></div>'
        f'<a class="btn btn-red" href="{SURVEY_URL}" target="_blank">Take the survey</a></div></div></div>'
        + footer_html(flush=True)
    )
    st.markdown(html, unsafe_allow_html=True)


def page_predictor():
    page_header("Effluent predictor", "Effluent quality predictor",
                "Enter the plant's readings. Fields you leave unchanged use the typical (median) value from the "
                "training data. Results update as you type.")
    if meta is None:
        st.error("No trained models found in the models/ folder. Train them first (see the guidebook).")
        st.stop()
    stats = meta["feature_stats"]
    inputs = {}
    left, right = st.columns(2, gap="medium")
    with left:
        with st.container(border=True, key="panel_4"):
            panel_title("Plant readings today")
            cols = st.columns(2)
            for i, f in enumerate(QUICK_INPUTS):
                s = stats[f]
                inputs[f] = cols[i % 2].number_input(s["label"], value=round(s["median"], 2), format="%.2f", key=f)
    with right:
        with st.container(border=True, key="panel_5"):
            panel_title("Recent effluent results")
            cols = st.columns(2)
            for i, f in enumerate(LAG_FEATURES):
                s = stats[f]
                inputs[f] = cols[i % 2].number_input(s["label"], value=round(s["median"], 2), format="%.2f", key=f)
    with st.expander("More plant readings (optional)"):
        cols = st.columns(3)
        others = [f for f in meta["features"] if f not in QUICK_INPUTS and f not in LAG_FEATURES]
        for i, f in enumerate(others):
            s = stats[f]
            inputs[f] = cols[i % 3].number_input(s["label"], value=round(s["median"], 2), format="%.2f", key=f)
    with st.container(border=True, key="panel_ph"):
        effluent_ph = st.slider("Measured effluent pH (for the limit check)", 5.0, 10.0, 7.5, 0.1)

    X = pd.DataFrame([inputs])[meta["features"]]
    preds = {t: max(0.0, float(models[t].predict(X)[0])) for t in models}
    outside = [stats[f]["label"] for f in meta["features"]
               if not (stats[f]["min"] <= inputs[f] <= stats[f]["max"])]

    with st.container(border=True, key="panel_6"):
        panel_title("Predicted treated-water quality")
        cols = st.columns(3)
        for c, (t, v) in zip(cols, preds.items()):
            m = meta["targets"][t]
            c.metric(f"Effluent {SHORT[t]} (mg/L)", f"{v:.1f}", help=f"Model: {m['best_model']}. "
                     f"Typical error ±{m['test_MAE']} mg/L on unseen days.")
        if outside:
            st.warning("Some inputs are outside the range seen in training, so this prediction is less reliable: "
                       + ", ".join(outside))
        table = check_limits({**preds, "pH": effluent_ph})
        verdict_box(table)
        st.altair_chart(limits_chart(preds), theme=None, width="stretch")
        with st.expander("Details for each standard"):
            st.dataframe(table, hide_index=True, width="stretch")

    with st.container(border=True, key="panel_7"):
        panel_title("What if one reading changes?",
                    "Pick a reading and see how the predicted effluent responds while everything else stays as entered")
        choice = st.selectbox("Reading to vary", QUICK_INPUTS + LAG_FEATURES,
                              format_func=lambda f: stats[f]["label"], index=QUICK_INPUTS.index("DQO-D"))
        lo, hi = stats[choice]["min"], stats[choice]["max"]
        grid = pd.DataFrame([inputs] * 40)
        grid[choice] = [lo + (hi - lo) * i / 39 for i in range(40)]
        curves = pd.concat([pd.DataFrame({"x": grid[choice], "Predicted mg/L": models[t].predict(grid[meta["features"]]),
                                          "Parameter": SHORT[t]}) for t in models])
        line = alt.Chart(curves).mark_line(strokeWidth=2.2).encode(
            x=alt.X("x:Q", title=stats[choice]["label"]),
            y=alt.Y("Predicted mg/L:Q"),
            color=alt.Color("Parameter:N", scale=alt.Scale(domain=["BOD", "COD", "TSS"], range=[LIVE, "#7A4FB5", TEAL]),
                            legend=alt.Legend(orient="bottom", title=None)),
            tooltip=[alt.Tooltip("x:Q", title="Input", format=".1f"), "Parameter",
                     alt.Tooltip("Predicted mg/L:Q", format=".1f")])
        rule = alt.Chart(pd.DataFrame({"x": [inputs[choice]]})).mark_rule(color=MUTED, strokeDash=[4, 4]).encode(x="x:Q")
        st.altair_chart(chart_style(line + rule, height=280), theme=None, width="stretch")
        st.caption("Dashed line: your current value. Models were trained on one European plant (1990–91); "
                   "a real plant should retrain them on its own data.")

    with st.expander("Batch prediction from a CSV file"):
        st.caption("Upload one row per day with the dataset's column codes (e.g. Q-E, DBO-E). If it also has DATE and "
                   "effluent columns (DBO-S, DQO-S, SS-S), recent effluent results are worked out automatically. "
                   "Missing columns are filled with typical values.")
        up = st.file_uploader("Upload CSV", type="csv")
        if up is not None:
            batch = pd.read_csv(up)
            if "DATE" in batch.columns and all(t in batch.columns for t in TARGETS):
                batch["DATE"] = pd.to_datetime(batch["DATE"], errors="coerce")
                batch = add_recent_effluent(batch)
            Xb = batch.reindex(columns=meta["features"])
            for f in meta["features"]:
                Xb[f] = pd.to_numeric(Xb[f], errors="coerce").fillna(stats[f]["median"])
            for t in models:
                batch[f"Predicted {SHORT[t]} (mg/L)"] = models[t].predict(Xb).clip(min=0).round(1)
            st.dataframe(batch, width="stretch")
            st.download_button("Download predictions", batch.to_csv(index=False), "predictions.csv", "text/csv")
    footer()


def page_reuse():
    page_header("Reuse checker", "Reuse checker",
                "Set the values from a lab report to see which uses the treated water allows.")
    with st.container(border=True, key="panel_8"):
        panel_title("Lab results")
        c1, c2 = st.columns(2, gap="large")
        bod = c1.slider("BOD₅ (mg/L)", 0.0, 150.0, 25.0, 0.5)
        cod = c2.slider("COD (mg/L)", 0.0, 300.0, 80.0, 1.0)
        tss = c1.slider("TSS (mg/L)", 0.0, 250.0, 20.0, 0.5)
        ph = c2.slider("pH", 4.0, 11.0, 7.4, 0.1)
    values = {"DBO-S": bod, "DQO-S": cod, "SS-S": tss}
    table = check_limits({**values, "pH": ph})
    with st.container(border=True, key="panel_9"):
        panel_title("Result")
        verdict_box(table)
        st.altair_chart(limits_chart({k: max(v, 1.0) for k, v in values.items()}), theme=None, width="stretch")
        st.dataframe(table, hide_index=True, width="stretch")
    with st.expander("Where do these limits come from?"):
        st.markdown(
            "- **Discharge to inland waters:** Pakistan's environmental quality standards for municipal and "
            "liquid industrial effluents (BOD₅ 80, COD 150, TSS 200 mg/L, pH 6–9), as also adopted in the "
            "Punjab and Sindh provincial standards.\n"
            "- **Irrigation:** US EPA (2012) *Guidelines for Water Reuse*: non-food or processed crops BOD ≤ 30, "
            "TSS ≤ 30 mg/L; food crops eaten raw BOD ≤ 10 mg/L and TSS ≤ 5 mg/L (when TSS is used instead of turbidity).\n"
            "- Real reuse also needs **pathogen** limits (E. coli or faecal coliforms, helminth eggs) "
            "following WHO (2006) guidelines. This tool checks only the chemical indicators."
        )
    footer()


def page_recovery():
    page_header("Resource recovery", "Resource recovery calculator",
                "Estimate what a treatment plant could recover each day. Every assumption is editable; replace it "
                "with a value from the studies you review.")
    with st.container(border=True, key="panel_10"):
        panel_title("Plant inputs")
        c1, c2 = st.columns(2, gap="large")
        flow = c1.slider("Wastewater flow (m³/day)", 1000, 200000, 10000, 1000)
        cod_in = c2.slider("Influent COD (mg/L)", 100, 1200, 500, 10)
        tn = c1.slider("Influent total nitrogen (mg/L)", 10, 120, 40, 1)
        tp = c2.slider("Influent total phosphorus (mg/L)", 1, 30, 8, 1)
    with st.expander("Assumptions (edit to match your literature)"):
        a1, a2 = st.columns(2)
        f_digest = a1.slider("Share of influent COD converted to methane (%)", 0, 80, 30) / 100
        ch4_frac = a2.slider("Methane content of biogas (%)", 50, 75, 65) / 100
        chp_eff = a1.slider("Electrical efficiency of the gas engine (%)", 20, 45, 35) / 100
        p_rec = a2.slider("Phosphorus recovered as struvite (%)", 0, 90, 40) / 100
        n_rec = a1.slider("Nitrogen recovered for fertiliser (%)", 0, 90, 20) / 100
        pha_yield = a2.number_input("PHA bioplastic yield (kg PHA per kg COD)", value=0.10,
                                    min_value=0.0, max_value=0.6, step=0.01)
        pha_cod = a1.slider("Share of influent COD sent to PHA production (%)", 0, 50, 10) / 100

    cod_load = flow * cod_in / 1000                       # kg COD/day
    ch4 = cod_load * f_digest * 0.35                      # m³ CH4/day (0.35 m³ CH4 per kg COD at STP)
    biogas = ch4 / ch4_frac if ch4_frac else 0
    energy_kwh = ch4 * 9.97                               # kWh/day (LHV ≈ 35.8 MJ/m³)
    elec_kwh = energy_kwh * chp_eff
    lpg_kg = ch4 * 35.8 / 46.0                            # LPG LHV ≈ 46 MJ/kg
    p_load, n_load = flow * tp / 1000, flow * tn / 1000   # kg/day
    struvite = p_load * p_rec * 245.41 / 30.97            # kg MgNH4PO4·6H2O/day
    n_fert = n_load * n_rec
    pha = cod_load * pha_cod * pha_yield

    with st.container(border=True, key="panel_11"):
        panel_title("Daily recovery potential")
        m1, m2, m3 = st.columns(3)
        m1.metric("Biogas (m³/day)", f"{biogas:,.0f}", f"{ch4:,.0f} m³ methane", delta_color="off", delta_arrow="off")
        m2.metric("Electricity (kWh/day)", f"{elec_kwh:,.0f}", f"≈ {elec_kwh / 1000 * 365:,.0f} MWh/year",
                  delta_color="off", delta_arrow="off")
        m3.metric("Cooking-gas equivalent (kg LPG/day)", f"{lpg_kg:,.0f}")
        m4, m5, m6 = st.columns(3)
        m4.metric("Struvite fertiliser (kg/day)", f"{struvite:,.0f}", f"{p_load * p_rec:,.1f} kg P",
                  delta_color="off", delta_arrow="off")
        m5.metric("Nitrogen for fertiliser (kg N/day)", f"{n_fert:,.0f}",
                  f"≈ {n_fert / 0.46:,.0f} kg urea-equivalent", delta_color="off", delta_arrow="off")
        m6.metric("PHA bioplastic (kg/day)", f"{pha:,.0f}")

    with st.container(border=True, key="panel_12"):
        panel_title("Over a year", "Tonnes recovered per year at the settings above")
        year = pd.DataFrame({
            "Product": ["Struvite fertiliser", "Nitrogen (as urea)", "PHA bioplastic", "LPG equivalent"],
            "Tonnes per year": [struvite * 365 / 1000, n_fert / 0.46 * 365 / 1000, pha * 365 / 1000,
                                lpg_kg * 365 / 1000],
        })
        bar = alt.Chart(year).mark_bar(color=LIVE, cornerRadiusEnd=3, height=22).encode(
            y=alt.Y("Product:N", sort="-x", title=None), x=alt.X("Tonnes per year:Q"),
            tooltip=["Product", alt.Tooltip("Tonnes per year:Q", format=",.1f")])
        st.altair_chart(chart_style(bar, height=190), theme=None, width="stretch")
    with st.expander("How is this calculated?"):
        st.markdown(
            "- COD load (kg/day) = flow × COD ÷ 1000\n"
            "- Methane = COD load × share converted × 0.35 m³ CH₄ per kg COD (theoretical value at 0 °C, 1 atm)\n"
            "- Energy = methane × 9.97 kWh/m³; electricity = energy × engine efficiency\n"
            "- Struvite = P recovered × 245.41 ÷ 30.97 (molar mass of MgNH₄PO₄·6H₂O ÷ P)\n"
            "- Urea-equivalent = N ÷ 0.46 (urea is 46 % N)\n"
            "- These are first-order estimates for teaching and screening, not a plant design."
        )
    footer()


def page_explorer():
    if data is None:
        page_header("Plant data", "Plant data explorer", "Run the data preparation step first.")
        st.error("Clean data not found. Run `python src/prepare_data.py` first.")
        st.stop()
    page_header("Plant data", "Plant data explorer",
                f"{len(data)} days of measurements from the studied plant, {data['DATE'].min():%B %Y} to "
                f"{data['DATE'].max():%B %Y}: how the plant performs, and every measurement over time.")
    plant_snapshot()
    with st.container(border=True, key="panel_13"):
        panel_title("Measurements over time")
        options = [c for c in LABELS if c in data.columns and not c.endswith(("_last", "_avg3"))]
        picked = st.multiselect("Measurements to show", options, default=["DBO-S", "SS-S"],
                                format_func=lambda c: LABELS[c])
        if picked:
            long = data[["DATE"] + picked].melt("DATE", var_name="code", value_name="value").dropna()
            long["Measurement"] = long["code"].map(LABELS)
            zoom = alt.selection_interval(encodings=["x"], bind="scales")
            ts = alt.Chart(long).mark_line(strokeWidth=1.5).encode(
                x=alt.X("DATE:T", title=None), y=alt.Y("value:Q", title="Value"),
                color=alt.Color("Measurement:N", scale=alt.Scale(range=[LIVE, TEAL, "#7A4FB5", WARN, NAVY]),
                                legend=alt.Legend(orient="bottom", title=None, labelLimit=320)),
                tooltip=[alt.Tooltip("DATE:T", format="%d %b %Y"), "Measurement",
                         alt.Tooltip("value:Q", format=".1f")],
            ).add_params(zoom)
            st.altair_chart(chart_style(ts, height=310), theme=None, width="stretch")

    with st.container(border=True, key="panel_14"):
        panel_title("How each stage lowers the load", "Spread of daily values at each sampling point")
        measure = st.radio("Measurement", ["BOD", "Suspended solids"], horizontal=True)
        code = "DBO" if measure == "BOD" else "SS"
        stage_names = {"E": "1 Raw sewage", "P": "2 Primary settler", "D": "3 Biological stage", "S": "4 Treated water"}
        stage = pd.concat([pd.DataFrame({"Stage": stage_names[p], "mg/L": data[f"{code}-{p}"]})
                           for p in ["E", "P", "D", "S"]]).dropna()
        box = alt.Chart(stage).mark_boxplot(color=LIVE, size=44, outliers={"color": GREY, "size": 10},
                                            median={"color": "#ffffff"}).encode(
            x=alt.X("Stage:N", title=None, sort=list(stage_names.values()), axis=alt.Axis(labelAngle=0)),
            y=alt.Y("mg/L:Q", scale=alt.Scale(type="log"), title=f"{measure} (mg/L, log scale)",
                    axis=alt.Axis(values=[2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000])))
        st.altair_chart(chart_style(box, height=300), theme=None, width="stretch")
        st.caption("Boxes show the middle half of days; whiskers and dots show the spread, including storm days.")
    footer()


def page_model():
    page_header("Model", "About the model",
                "Two benchmarks and four learning models compared on 527 days of plant data, tested on the final "
                "20% of days the models never saw.")
    if meta is None:
        st.error("Models not trained yet.")
        st.stop()
    with st.container(border=True, key="panel_15"):
        panel_title("Selected model for each parameter")
        st.markdown(
            "Inputs are the day's readings taken before the final effluent (plant inflow, primary settler and "
            "secondary settler) plus the plant's recent effluent results. Two benchmarks (typical value, last result) "
            "and four learning models (ridge regression, random forest, XGBoost and their average) were compared with "
            "5-fold time-series cross-validation on log-scaled data; the last 20% of days were held back as a test set.")
        summary = pd.DataFrame([
            {"Parameter": m["name"], "Selected model": m["best_model"], "Test R²": m["test_R2"],
             "Test MAE (mg/L)": m["test_MAE"], "Test RMSE (mg/L)": m["test_RMSE"], "Days used": m["n_days"]}
            for m in meta["targets"].values()
        ])
        st.dataframe(summary, hide_index=True, width="stretch")
    comp = TABLES_DIR / "table2_model_comparison.csv"
    if comp.exists():
        cmp_df = pd.read_csv(comp)
        with st.container(border=True, key="panel_16"):
            panel_title("How every model did on the held-out days", "Lower error is better")
            target = st.radio("Parameter", list(cmp_df["target"].unique()), horizontal=True)
            sub = cmp_df[cmp_df["target"] == target].copy()
            sub["Kind"] = sub["model"].map(lambda m: "Benchmark" if m in ("Baseline (median)", "Last result")
                                           else "Learning model")
            chart = alt.Chart(sub).mark_bar(cornerRadiusEnd=3, height=20).encode(
                y=alt.Y("model:N", sort="x", title=None), x=alt.X("Test_MAE:Q", title="Test MAE (mg/L)"),
                color=alt.Color("Kind:N", scale=alt.Scale(domain=["Learning model", "Benchmark"], range=[LIVE, GREY]),
                                legend=alt.Legend(orient="bottom", title=None)),
                tooltip=["model", alt.Tooltip("Test_MAE:Q", format=".2f"), alt.Tooltip("Test_R2:Q", format=".2f"),
                         alt.Tooltip("CV_MAE_mean:Q", format=".2f", title="CV MAE")])
            st.altair_chart(chart_style(chart, height=240), theme=None, width="stretch")
            with st.expander("Full comparison table"):
                st.dataframe(cmp_df, hide_index=True, width="stretch")
    with st.container(border=True, key="panel_17"):
        panel_title("Figures for your paper", "The same figures saved in results/figures, ready for Word and slides")
        tabs = st.tabs([f"Effluent {SHORT[t]}" for t in TARGETS])
        for tab, t in zip(tabs, TARGETS):
            with tab:
                cols = st.columns(2)
                for c, fig in zip(cols, [f"fig_obs_vs_pred_{t}.png", f"fig_importance_{t}.png"]):
                    p = FIGURES_DIR / fig
                    if p.exists():
                        c.image(str(p), width="stretch")
    footer()


def page_survey():
    page_header("Survey", "Learn and take the survey",
                "Why treated wastewater matters, what the risks are, and how you can help our research.")
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with st.container(border=True, key="panel_18"):
            panel_title("Why reuse wastewater?")
            st.markdown(
                "Wastewater carries water, energy (organic matter becomes biogas) and nutrients (nitrogen and "
                "phosphorus become fertiliser). A circular bioeconomy treats it as a resource: clean water for "
                "irrigation, energy for the plant, fertiliser for farms and even raw material for biodegradable plastics.")
    with c2:
        with st.container(border=True, key="panel_19"):
            panel_title("What are the risks?")
            st.markdown(
                "- **Pathogens:** bacteria, viruses and parasite eggs in raw sewage, removed by treatment and disinfection.\n"
                "- **Antibiotics and resistance genes (ARGs):** plants receive both and can release resistant bacteria "
                "if treatment is incomplete.\n"
                "- **Microplastics:** most are trapped in sludge, so sludge used on land needs care.\n"
                "- **Heavy metals and chemicals:** mainly from industrial wastewater.")
    with st.container(border=True, key="panel_20"):
        panel_title("Help our research", "About 5 minutes, anonymous, adults 18+")
        st.markdown("We are studying how people in Pakistan feel about reusing treated wastewater.")
        st.link_button("Take the survey", SURVEY_URL, type="primary")
    footer()


# ---------------------------------------------------------------------------
# Navigation (custom top bar)
# ---------------------------------------------------------------------------
PAGES = {
    "home": st.Page(page_home, title="Home", url_path="home", default=True),
    "predictor": st.Page(page_predictor, title="Effluent predictor", url_path="predictor"),
    "reuse": st.Page(page_reuse, title="Reuse checker", url_path="reuse"),
    "recovery": st.Page(page_recovery, title="Resource recovery", url_path="recovery"),
    "explorer": st.Page(page_explorer, title="Plant data", url_path="plant-data"),
    "model": st.Page(page_model, title="About the model", url_path="model"),
    "survey": st.Page(page_survey, title="Learn & survey", url_path="survey"),
}
PAGE_TITLES = {k: p.title for k, p in PAGES.items()}
NAV_LABELS = {"home": "Home", "predictor": "Predictor", "reuse": "Reuse", "recovery": "Recovery",
              "explorer": "Plant data", "model": "Model", "survey": "Take the survey"}

style()
current = st.navigation(list(PAGES.values()), position="hidden")
topbar(current.title)
current.run()
