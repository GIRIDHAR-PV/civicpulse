import streamlit as st, hashlib, os, difflib
import numpy as np
import psycopg2, psycopg2.extras, psycopg2.pool
from psycopg2.extensions import register_adapter, AsIs
from zoneinfo import ZoneInfo
from html import escape
import pathlib

try:  # force a light theme so every widget stays readable (takes full effect from the next launch)
    _cfg = pathlib.Path(".streamlit/config.toml")
    if not _cfg.exists():
        _cfg.parent.mkdir(exist_ok=True)
        _cfg.write_text('[theme]\nbase = "light"\nprimaryColor = "#dc2626"\nbackgroundColor = "#f8f8fa"\n'
                        'secondaryBackgroundColor = "#ffffff"\ntextColor = "#1c1917"\n')
    for _k, _v in {"base": "light", "primaryColor": "#dc2626", "backgroundColor": "#f8f8fa",
                   "secondaryBackgroundColor": "#ffffff", "textColor": "#1c1917"}.items():
        st._config.set_option(f"theme.{_k}", _v)
except Exception:
    pass
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, time

IST = ZoneInfo("Asia/Kolkata")  # cloud servers run on UTC; the app should run on Indian time
register_adapter(np.int64, AsIs); register_adapter(np.float64, AsIs)
CATS = ["Road / Pothole", "Garbage / Sanitation", "Water Supply", "Drainage / Sewage",
        "Street Light / Electricity", "Public Safety", "Other"]
HIGH = ["fire", "accident", "live wire", "shock", "gas leak", "flood", "open manhole", "collapse", "injur"]
MED = ["pothole", "no water", "leak", "garbage", "overflow", "blocked", "broken", "dark", "stray"]
LEVEL = {1: "Low", 2: "Medium", 3: "High"}
STATUS = ["Pending", "In Progress", "Resolved", "Rejected"]
PC = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}
SC = {"Pending": "#f59e0b", "In Progress": "#3b82f6", "Resolved": "#22c55e", "Rejected": "#94a3b8"}
CSS = """<style>
#MainMenu, footer {visibility: hidden;}
:root {color-scheme: light;}
@keyframes rise {from {opacity: 0; transform: translateY(12px);} to {opacity: 1; transform: none;}}
@keyframes slide {to {background-position: 200% 0;}}
@keyframes float {0%, 100% {transform: translateY(0);} 50% {transform: translateY(-10px);}}
@keyframes beat {0%, 100% {transform: scale(1);} 50% {transform: scale(1.14);}}
.stApp {background-color: #f8f8fa; background-image: radial-gradient(#e4e4e7 1px, transparent 1px); background-size: 22px 22px;}
.stApp, .stApp p, .stApp span, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp small {color: #1c1917;}
.stApp [data-testid="stCaptionContainer"] * {color: #57534e;}
::placeholder {color: #a8a29e !important; opacity: 1;}
.stApp input, .stApp textarea, .stApp [data-baseweb="select"] > div, .stApp [data-baseweb="input"] {
  background: #fff !important; border-radius: 10px;}
.stApp [data-baseweb="select"] *, .stApp input, .stApp textarea {color: #1c1917 !important;}
.stApp input:focus, .stApp textarea:focus {box-shadow: 0 0 0 3px #fca5a588;}
[data-baseweb="popover"] ul, [data-baseweb="popover"] li, [data-baseweb="menu"] {background: #fff !important;}
[data-baseweb="popover"] li, [data-baseweb="popover"] li * {color: #1c1917 !important;}
[data-baseweb="popover"] li:hover {background: #fee2e2 !important;}
[data-testid="stFileUploaderDropzone"] {background: #fff;} [data-testid="stFileUploaderDropzone"] * {color: #1c1917 !important;}
[data-testid="stHeader"] {background: transparent;}
.block-container {padding-top: 2rem; max-width: 1250px;}
[data-testid="stSidebar"] {background: #7f1d1d;}
[data-testid="stSidebar"] * {color: #ffffff !important;}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"], [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
  width: 100%; justify-content: flex-start; text-align: left; border-radius: 10px; padding: .65rem 1rem; font-weight: 500;
  background: rgba(255,255,255,.1) !important; border: 1px solid rgba(255,255,255,.3) !important; transition: all .18s ease;}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {background: rgba(255,255,255,.22) !important;
  border-color: #fff !important; transform: translateX(4px);}
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {background: #dc2626 !important; border: 1px solid #fca5a5 !important;
  font-weight: 700; box-shadow: 0 4px 14px rgba(0,0,0,.3);}
.navlabel {font-size: .7rem; letter-spacing: 2px; color: #fecaca !important; margin: 14px 0 6px;}
[data-testid="stMetric"] {background: #fff; border: 1px solid #e5e7eb; border-top: 4px solid #dc2626; border-radius: 12px;
  padding: 14px 18px; animation: rise .5s ease both; transition: transform .2s, box-shadow .2s;}
[data-testid="stMetric"]:hover {transform: translateY(-4px); box-shadow: 0 10px 22px rgba(0,0,0,.1);}
[data-testid="stMetricLabel"] p {color: #57534e !important; font-weight: 600;}
[data-testid="stMetricValue"] * {color: #1c1917 !important;}
[data-testid="stVerticalBlockBorderWrapper"] {background: #fff; border-radius: 12px; transition: box-shadow .2s;}
[data-testid="stVerticalBlockBorderWrapper"]:hover {box-shadow: 0 8px 20px rgba(0,0,0,.08); border-color: #fca5a5;}
[data-testid="stImage"] img, [data-testid="stImageContainer"] img {border-radius: 12px; background: #fff;
  box-shadow: 0 2px 10px rgba(0,0,0,.07);}
.stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"]>button {border-radius: 10px; border: 0;
  background: #dc2626; font-weight: 700; padding: .45rem 1.2rem; transition: all .18s ease;}
.stButton>button, .stButton>button p, .stDownloadButton>button, .stDownloadButton>button p,
[data-testid="stFormSubmitButton"]>button, [data-testid="stFormSubmitButton"]>button p {color: #ffffff !important;}
.stButton>button:hover, .stDownloadButton>button:hover, [data-testid="stFormSubmitButton"]>button:hover {
  background: #b91c1c; transform: translateY(-2px); box-shadow: 0 6px 14px rgba(185,28,28,.3);}
.stButton>button:active {transform: scale(.97);}
.stButton>button:disabled {background: #e5e7eb; transform: none; box-shadow: none;}
.stButton>button:disabled, .stButton>button:disabled p {color: #78716c !important;}
button[data-baseweb="tab"] {padding: 10px 14px; border-radius: 8px 8px 0 0; transition: background .2s;}
button[data-baseweb="tab"]:hover {background: #fee2e2;}
button[data-baseweb="tab"] p {color: #44403c !important; font-weight: 600;}
button[data-baseweb="tab"][aria-selected="true"] p {color: #b91c1c !important; font-weight: 800;}
[data-baseweb="tab-highlight"] {background: #dc2626; height: 3px;}
[data-testid="stAlert"] {background: #fff; border: 1px solid #e5e7eb; border-left: 6px solid #dc2626; border-radius: 12px;}
[data-testid="stAlert"] * {color: #1c1917 !important;}
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) {border-left-color: #22c55e;}
[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) {border-left-color: #3b82f6;}
.hero {position: relative; overflow: hidden; background: #fff; border: 1px solid #e5e7eb; border-left: 6px solid #dc2626;
  padding: 20px 26px 24px; border-radius: 12px; margin-bottom: 18px; animation: rise .5s ease both; box-shadow: 0 4px 16px rgba(0,0,0,.06);}
.hero::before {content: ""; position: absolute; right: -40px; top: -60px; width: 190px; height: 190px; border-radius: 50%;
  background: rgba(220,38,38,.08); animation: float 5s ease-in-out infinite;}
.hero::after {content: ""; position: absolute; left: 0; bottom: 0; width: 100%; height: 3px; background-size: 200% 100%;
  background-image: linear-gradient(90deg, #dc2626, #fca5a5, #dc2626); animation: slide 3s linear infinite;}
.hero h1 {margin: 0; font-size: 1.6rem; color: #7f1d1d !important; position: relative;}
.hero p {margin: 4px 0 0; color: #57534e !important; position: relative;}
.hero.big {padding: 44px 36px 40px; text-align: center; border-left: 1px solid #e5e7eb; border-top: 6px solid #dc2626;}
.hero.big h1 {font-size: 2.7rem;}
.chips span {display: inline-block; background: #fef2f2; border: 1px solid #fecaca; color: #991b1b !important; padding: 6px 15px;
  border-radius: 999px; margin: 12px 5px 0; font-size: .85rem; position: relative; transition: all .2s;}
.chips span:hover {background: #dc2626; color: #fff !important; transform: translateY(-4px); border-color: #dc2626;}
.pill {padding: 2px 10px; border-radius: 6px; font-size: .75rem; font-weight: 700; color: #fff !important;}
.tblwrap {overflow: auto; background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,.05);
  margin-bottom: 14px;}
.tbl {border-collapse: collapse; width: 100%; font-size: .88rem;}
.tbl th {position: sticky; top: 0; background: #fef2f2; color: #7f1d1d !important; text-align: left !important; padding: 11px 14px;
  white-space: nowrap; border-bottom: 2px solid #dc2626;}
.tbl td {padding: 9px 14px; border-top: 1px solid #f3f4f6; color: #1c1917; background: #fff;}
.tbl tr:nth-child(even) td {background: #fafafa;}
.tbl tr:hover td {background: #fee2e2; transition: background .15s;}
.podium {display: flex; gap: 16px; margin: 6px 0 22px; flex-wrap: wrap;}
.pod {flex: 1; min-width: 180px; background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 18px; text-align: center;
  animation: rise .5s ease both; transition: transform .2s, box-shadow .2s;}
.pod:hover {transform: translateY(-6px); box-shadow: 0 12px 26px rgba(0,0,0,.12);}
.pod.first {border: 2px solid #dc2626; background: #fef2f2;}
.pod .rank {font-weight: 800; letter-spacing: 2px; color: #dc2626;}
.pod .pts {font-size: 1.5rem; font-weight: 800;}
.pod h3 {margin: 6px 0;}
.brand {display: flex; flex-direction: column; align-items: center; gap: 4px; margin: 34px 0 8px; text-align: center;}
.brand .row {display: flex; align-items: center; gap: 12px;}
.brand svg {animation: beat 1.6s ease-in-out infinite; filter: drop-shadow(0 4px 8px rgba(185,28,28,.35));}
.brand .name {font-size: 1.7rem; font-weight: 800; letter-spacing: -.5px;}
.brand .name b {color: #dc2626;}
.brand .tag {color: #57534e; font-size: .9rem;}
.brand .copy {color: #a8a29e !important; font-size: .75rem; margin-top: 6px;}
</style>"""


def hero(title, sub=""):
    st.markdown(f'<div class="hero"><h1>{title}</h1>{f"<p>{sub}</p>" if sub else ""}</div>', unsafe_allow_html=True)


def pill(t):
    return f'<span class="pill" style="background:{PC.get(t) or SC.get(t, "#64748b")}">{t}</span>'


plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "#ffffff",
                     "axes.facecolor": "#ffffff", "axes.titleweight": "bold", "axes.titlesize": 11,
                     "axes.prop_cycle": plt.cycler(color=["#dc2626", "#1c1917", "#f97316", "#7f1d1d", "#78716c", "#fb7185"])})


def table(df, h=460):
    """Light, hoverable HTML table (always readable, whatever the browser theme)."""
    d = df.copy()
    d.columns = [str(c).replace("_", " ").title().replace(" Id", " ID") for c in d.columns]
    html = d.to_html(index=False, border=0, classes="tbl", na_rep="-").replace("\n", " ")
    st.markdown(f'<div class="tblwrap" style="max-height:{h}px">{html}</div>', unsafe_allow_html=True)


def mplot(data, kind="bar", color=None, stacked=False, h=3.2):
    fig, ax = plt.subplots(figsize=(7, h))
    data.plot(kind=kind, ax=ax, color=color, stacked=stacked, rot=0 if kind == "line" else 25,
              legend=isinstance(data, pd.DataFrame), **({"marker": "o"} if kind == "line" else {}))
    ax.set_xlabel("")
    ax.grid(axis="y", alpha=.25)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


OPEN = ["Pending", "In Progress"]
SLA = {"High": 2, "Medium": 5, "Low": 10}  # days allowed before a report counts as overdue
AREAS = {"Adyar": (13.0012, 80.2565), "T. Nagar": (13.0418, 80.2341), "Velachery": (12.9815, 80.2180),
         "Anna Nagar": (13.0850, 80.2101), "Tambaram": (12.9249, 80.1000), "Guindy": (13.0067, 80.2206),
         "Mylapore": (13.0368, 80.2676), "Porur": (13.0382, 80.1565), "Chromepet": (12.9516, 80.1462),
         "Perambur": (13.1143, 80.2329), "Sholinganallur": (12.9010, 80.2279), "Kodambakkam": (13.0521, 80.2255)}


# ---------- database (Supabase Postgres) ----------
@st.cache_resource
def _pool():
    cfg = dict(st.secrets["db"])
    return psycopg2.pool.ThreadedConnectionPool(1, 8, sslmode="require", **cfg)


class db:
    """Small wrapper so the code reads like before: `with db() as c: c.execute(sql, params)`.
    Uses ? placeholders, commits on exit (rolls back on error) and hands the connection back to the pool."""

    def __enter__(self):
        p = _pool()
        for _ in range(3):
            self.conn = p.getconn()
            try:  # drop connections the server has silently closed
                with self.conn.cursor() as cur:
                    cur.execute("SELECT 1")
                self.conn.rollback()
                return self
            except Exception:
                p.putconn(self.conn, close=True)
        raise RuntimeError("Could not connect to the database.")

    def execute(self, sql, params=()):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(sql.replace("?", "%s"), params)
        return cur

    def executemany(self, sql, rows):
        cur = self.conn.cursor()
        cur.executemany(sql.replace("?", "%s"), rows)

    def __exit__(self, et, ev, tb):
        self.conn.rollback() if et else self.conn.commit()
        _pool().putconn(self.conn)


def read(sql, params=()):
    """Run a SELECT and return a DataFrame."""
    with db() as c:
        cur = c.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame([list(r) for r in cur.fetchall()], columns=cols)


def hash_pw(p, salt):
    return hashlib.pbkdf2_hmac("sha256", p.encode(), bytes.fromhex(salt), 100_000).hex()


def add_user(u, p, role="citizen"):
    salt = os.urandom(8).hex()
    try:
        with db() as c:
            c.execute("INSERT INTO users(username,password,salt,role) VALUES(?,?,?,?)",
                      (u.strip(), hash_pw(p, salt), salt, role))
        return True
    except psycopg2.IntegrityError:
        return False


def add_worker(u, p, name, phone, skill, start, end):
    if not add_user(u, p, "worker"):
        return False
    with db() as c:
        uid = c.execute("SELECT user_id FROM users WHERE username=?", (u.strip(),)).fetchone()[0]
        c.execute("INSERT INTO workers VALUES(?,?,?,?,?,?)", (uid, name, phone, skill, start, end))
    return True


@st.cache_resource
def init():
    """Create tables and seed the admin + demo workers (runs once per server start)."""
    with db() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS users(user_id SERIAL PRIMARY KEY,
            username TEXT UNIQUE, password TEXT, salt TEXT, role TEXT);
        CREATE TABLE IF NOT EXISTS reports(report_id SERIAL PRIMARY KEY,
            user_id INTEGER, category TEXT, location TEXT, area TEXT, description TEXT,
            image TEXT, date TEXT, priority TEXT DEFAULT 'Low', status TEXT DEFAULT 'Pending',
            duplicate_of INTEGER, dup_count INTEGER DEFAULT 0, resolved_on TEXT,
            assigned_to INTEGER, scheduled TEXT);
        CREATE TABLE IF NOT EXISTS images(report_id INTEGER PRIMARY KEY, data BYTEA);
        CREATE TABLE IF NOT EXISTS votes(report_id INTEGER, user_id INTEGER, UNIQUE(report_id,user_id));
        CREATE TABLE IF NOT EXISTS workers(user_id INTEGER PRIMARY KEY, full_name TEXT, phone TEXT,
            skill TEXT, shift_start TEXT, shift_end TEXT);
        CREATE TABLE IF NOT EXISTS notifications(id SERIAL PRIMARY KEY,
            user_id INTEGER, message TEXT, date TEXT, seen INTEGER DEFAULT 0);""")
        has_admin = c.execute("SELECT 1 FROM users WHERE username='admin'").fetchone()
        has_workers = c.execute("SELECT 1 FROM workers").fetchone()
    if not has_admin:
        add_user("admin", "admin123", "admin")
    if not has_workers:
        for w in [("ravi.kumar", "Ravi Kumar", "98400 11111", "Road / Pothole", "09:00", "17:00"),
                  ("meena.s", "Meena S", "98400 22222", "Garbage / Sanitation", "06:00", "14:00"),
                  ("arun.p", "Arun P", "98400 33333", "Water Supply", "10:00", "18:00"),
                  ("kavitha.r", "Kavitha R", "98400 44444", "Street Light / Electricity", "12:00", "20:00"),
                  ("suresh.m", "Suresh M", "98400 55555", "Drainage / Sewage", "08:00", "16:00")]:
            add_worker(w[0], "worker123", *w[1:])
    return True


def photo(rid, **kw):
    """Show the photo stored in the database for a report."""
    with db() as c:
        r = c.execute("SELECT data FROM images WHERE report_id=?", (int(rid),)).fetchone()
    if r:
        st.image(bytes(r[0]), **kw)


def now():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M")


def notify(uid, msg):
    with db() as c:
        c.execute("INSERT INTO notifications(user_id,message,date) VALUES(?,?,?)", (int(uid), msg, now()))


def set_status(rid, new, who="the admin"):
    """Change a report's status and notify the citizen who reported it."""
    with db() as c:
        r = c.execute("SELECT user_id,category,area FROM reports WHERE report_id=?", (rid,)).fetchone()
        c.execute("UPDATE reports SET status=?, resolved_on=? WHERE report_id=?",
                  (new, now() if new == "Resolved" else None, rid))
    tag = f"#{rid} ({r['category']}, {r['area']})"
    msg = {"Resolved": f"Good news! Your report {tag} has been resolved by {who}.",
           "In Progress": f"Work has started on your report {tag} ({who}).",
           "Rejected": f"Your report {tag} was closed as not actionable."}.get(new)
    if msg:
        notify(r["user_id"], msg)


def login(u, p):
    with db() as c:
        r = c.execute("SELECT * FROM users WHERE username=?", (u.strip(),)).fetchone()
    return r if r and hash_pw(p, r["salt"]) == r["password"] else None


# ---------- analysis (Pandas + rule-based) ----------
def refresh_priorities():
    """Re-score every report: keyword rules + repeat reports in the area + community upvotes."""
    df = load()
    if df.empty:
        return
    df["grp"] = df.category.str.lower() + "|" + df.area.str.lower().str.strip()
    df["freq"] = df.groupby("grp")["report_id"].transform("count")

    def score(r):
        t = r.description.lower()
        s = 3 if r.category == "Public Safety" or any(k in t for k in HIGH) else \
            2 if any(k in t for k in MED) else 1
        if r.freq >= 4 or r.votes >= 5: s = 3
        elif r.freq >= 2 or r.votes >= 2: s = max(s, 2)
        return LEVEL[s]

    df["priority"] = df.apply(score, axis=1)
    with db() as c:
        c.executemany("UPDATE reports SET priority=?, dup_count=? WHERE report_id=?",
                      [(r.priority, r.freq - 1, r.report_id) for r in df.itertuples()])


def find_duplicate(cat, area, desc):
    with db() as c:
        rows = c.execute("SELECT report_id, description FROM reports WHERE lower(category)=? AND lower(area)=?",
                         (cat.lower(), area.lower().strip())).fetchall()
    best = max(((difflib.SequenceMatcher(None, desc.lower(), r["description"].lower()).ratio(), r["report_id"])
                for r in rows), default=(0, None))
    return best[1] if best[0] >= 0.6 else None


def load(user_id=None):
    q = """SELECT r.*, u.username, w.full_name AS assigned_worker,
           (SELECT COUNT(*) FROM votes v WHERE v.report_id=r.report_id) AS votes
           FROM reports r JOIN users u ON u.user_id=r.user_id
           LEFT JOIN workers w ON w.user_id=r.assigned_to"""
    q, a = (q + " WHERE r.user_id=?", (user_id,)) if user_id else (q, ())
    return read(q + " ORDER BY r.report_id DESC", a)


def badge(pts):
    return "Civic Hero" if pts >= 50 else "Active Citizen" if pts >= 20 else "Newcomer"


def leaderboard(df):
    g = df.groupby("username").agg(reports=("report_id", "count"), upvotes=("votes", "sum"),
                                   resolved=("status", lambda x: (x == "Resolved").sum()))
    g["points"] = g.reports * 10 + g.upvotes * 2 + g.resolved * 5
    g["badge"] = g.points.map(badge)
    return g.sort_values("points", ascending=False).reset_index()


# ---------- pages ----------
def page_auth():
    st.markdown("""<div class="hero big"><h1>CivicPulse</h1>
      <p>Discover unreported local problems and get them fixed, faster.</p>
      <div class="chips"><span>Report in seconds</span><span>Smart worker assignment</span>
      <span>Live notifications</span><span>Area-wise insights</span></div></div>""", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2.4, 1])
    with mid:
        tabs = st.tabs(["Admin", "Citizen", "Worker", "Register"])
        for t, (role, k, hint) in zip(tabs, [("admin", "a", "Demo: admin / admin123"), ("citizen", "c", ""),
                                             ("worker", "w", "Demo: ravi.kumar / worker123")]):
            with t:
                u = st.text_input("Username", key=f"{k}u")
                p = st.text_input("Password", type="password", key=f"{k}p")
                if hint: st.caption(hint)
                if st.button(f"Login as {role}", key=f"{k}b"):
                    r = login(u, p)
                    if r and r["role"] == role:
                        st.session_state.user, st.session_state.welcome = dict(r), True
                        st.rerun()
                    st.error(f"Wrong tab: this account is not registered as {role}." if r else "Wrong username or password.")
        with tabs[3]:
            u = st.text_input("Choose a username", key="ru")
            p = st.text_input("Choose a password (min 6 chars)", type="password", key="rp")
            if st.button("Create account", key="rb"):
                if not u.strip() or len(p) < 6:
                    st.error("Enter a username and a password of at least 6 characters.")
                elif add_user(u, p):
                    st.success("Account created. Use the Citizen tab to log in.")
                else:
                    st.error("That username is taken.")
    footer()


def page_submit():
    hero("Report a local problem")
    with st.form("rep", clear_on_submit=True):
        cat = st.selectbox("Category", CATS)
        area = st.selectbox("Area / locality", list(AREAS) + ["Other"])
        if area == "Other": area = st.text_input("Type your area") or "Other"
        loc = st.text_input("Exact location / landmark")
        desc = st.text_area("Describe the problem")
        img = st.file_uploader("Photo (optional)", type=["jpg", "jpeg", "png"])
        if st.form_submit_button("Submit report"):
            if len(desc.strip()) < 10:
                st.error("Please describe the problem (at least 10 characters).")
                return
            if img and img.size > 3_000_000:
                st.error("Photo is too large. Please upload one under 3 MB.")
                return
            dup = find_duplicate(cat, area, desc)
            with db() as c:
                rid = c.execute("""INSERT INTO reports(user_id,category,location,area,description,image,date,duplicate_of)
                                   VALUES(?,?,?,?,?,?,?,?) RETURNING report_id""",
                                (st.session_state.user["user_id"], cat, loc, area.strip(), desc.strip(),
                                 "db" if img else None, now(), dup)).fetchone()[0]
                if img:
                    c.execute("INSERT INTO images VALUES(?,?)", (rid, psycopg2.Binary(img.getvalue())))
            refresh_priorities()
            st.success(f"Report #{rid} submitted.")
            if dup:
                st.info(f"Similar to report #{dup}, so it was flagged as a possible duplicate.")


def show_table(df):
    cols = ["report_id", "date", "category", "area", "description", "votes", "priority", "status", "assigned_worker", "scheduled"]
    if "username" in df: cols.insert(1, "username")
    d = df[cols].copy()
    d["priority"] = d.priority.map({"High": "High", "Medium": "Medium", "Low": "Low"})
    d["status"] = d.status.map({"Pending": "Pending", "In Progress": "In Progress", "Resolved": "Resolved",
                                "Rejected": "Rejected"})
    table(d)


def page_my():
    hero("My reports")
    df = load(st.session_state.user["user_id"])
    if df.empty:
        st.info("You haven't submitted anything yet.")
        return
    me = leaderboard(df).iloc[0]
    x, y, z = st.columns(3)
    x.metric("Your points", me.points); y.metric("Badge", me.badge); z.metric("Upvotes received", me.upvotes)
    show_table(df)
    for r in df.dropna(subset=["image"]).itertuples():
        with st.expander(f"Photo for report #{r.report_id}"):
            photo(r.report_id)


def area_stats(df):
    g = df.groupby("area").agg(total=("report_id", "count"), pending=("status", lambda x: (x != "Resolved").sum()),
                               high=("priority", lambda x: (x == "High").sum()),
                               top_issue=("category", lambda x: x.mode()[0])).reset_index()
    g["resolved_%"] = ((g.total - g.pending) / g.total * 100).round(0)
    g["lat"] = g.area.map(lambda a: AREAS.get(a, (None, None))[0])
    g["lon"] = g.area.map(lambda a: AREAS.get(a, (None, None))[1])
    return g.sort_values("total", ascending=False)


def page_area():
    hero("Area-wise insights")
    df = load()
    if df.empty:
        st.info("No reports yet.")
        return
    g = area_stats(df)
    st.subheader("Complaints registered per area")
    mplot(g.set_index("area")["total"], color="#dc2626")
    m = g.dropna(subset=["lat"]).assign(size=lambda d: d.total * 250)
    if not m.empty:
        st.map(m, latitude="lat", longitude="lon", size="size")
    table(g.drop(columns=["lat", "lon"]))
    st.subheader("Look up one area")
    a = st.selectbox("Choose area", g.area)
    d = df[df.area == a]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Complaints in {a}", len(d)); c2.metric("Unresolved", (d.status != "Resolved").sum())
    c3.metric("High priority", (d.priority == "High").sum()); c4.metric("Top issue", d.category.mode()[0])
    mplot(d.category.value_counts(), color="#dc2626")


def page_board():
    hero("Community board")
    st.caption("Facing the same problem? Press 'I face this too' — more votes push the priority up.")
    df = load()
    a = st.selectbox("Area", ["All"] + sorted(df.area.unique()) if not df.empty else ["All"])
    df = df if a == "All" else df[df.area == a]
    uid = st.session_state.user["user_id"]
    for r in df.sort_values("votes", ascending=False).head(15).itertuples():
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"**#{r.report_id} · {r.category}** — {escape(r.area)} · {pill(r.priority)} {pill(r.status)}\n\n{escape(r.description)}", unsafe_allow_html=True)
            if c2.button(f"Upvote ({r.votes})", key=f"v{r.report_id}", disabled=r.user_id == uid,
                         help="I face this too" if r.user_id != uid else "Your own report"):
                with db() as c:
                    c.execute("INSERT INTO votes VALUES(?,?) ON CONFLICT DO NOTHING", (r.report_id, uid))
                refresh_priorities()
                st.rerun()


def page_leaders():
    hero("Top contributors", "10 points per report, 2 per upvote received, 5 per resolved report")
    df = load()
    if df.empty:
        st.info("No reports yet.")
        return
    lb = leaderboard(df)
    cards = "".join(f'<div class="pod{" first" if i == 0 else ""}"><div class="rank">{["1st", "2nd", "3rd"][i]}</div>'
                    f'<h3>{escape(r.username)}</h3><div class="pts">{r.points} pts</div><div>{r.badge}</div></div>'
                    for i, r in enumerate(lb.head(3).itertuples()))
    st.markdown(f'<div class="podium">{cards}</div>', unsafe_allow_html=True)
    lb.insert(0, "rank", range(1, len(lb) + 1))
    table(lb[["rank", "username", "points", "badge", "reports", "upvotes", "resolved"]].rename(columns={"username": "citizen"}))


def page_dash():
    hero("Admin dashboard")
    df = load()
    if df.empty:
        st.info("No reports yet.")
        st.subheader("Worker availability")
        worker_board()
        return
    df["dt"] = pd.to_datetime(df.date)
    open_ = df.status.isin(["Pending", "In Progress"])
    df["overdue"] = open_ & ((pd.Timestamp.now(tz=IST).tz_localize(None) - df.dt).dt.days > df.priority.map(SLA))
    res = df[df.status == "Resolved"]
    days = ((pd.to_datetime(res.resolved_on) - res.dt).dt.total_seconds() / 86400).mean() if len(res) else 0
    k = st.columns(7)
    k[0].metric("Total", len(df)); k[1].metric("Pending", (df.status == "Pending").sum())
    k[2].metric("High priority", (df.priority == "High").sum()); k[3].metric("Duplicates", df.duplicate_of.notna().sum())
    k[4].metric("Resolution rate", f"{len(res) / len(df):.0%}"); k[5].metric("Overdue (SLA)", int(df.overdue.sum())); k[6].metric("Unassigned", int((df.assigned_to.isna() & open_).sum()))

    g = area_stats(df)
    st.info(f"**{g.iloc[0].area}** has the most complaints ({g.iloc[0].total}) · most common issue overall: "
            f"**{df.category.mode()[0]}** · avg resolution time: **{days:.1f} days** · "
            f"most upvoted: **#{df.sort_values('votes').iloc[-1].report_id}** ({df.votes.max()} votes)")

    st.subheader("Worker availability")
    worker_board()

    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    pv, sv = df.priority.value_counts(), df.status.value_counts()
    df.category.value_counts().plot.barh(ax=ax[0], title="Complaints by category", color="#dc2626")
    pv.plot.pie(ax=ax[1], title="Priority mix", autopct="%d%%", ylabel="", colors=[PC[i] for i in pv.index],
                wedgeprops={"width": 0.45, "edgecolor": "#ffffff"}, textprops={"color": "#1f2937"})
    sv.plot.bar(ax=ax[2], title="Status", color=[SC[i] for i in sv.index], rot=15)
    fig.tight_layout()
    st.pyplot(fig)

    t1, t2 = st.columns(2)
    with t1:
        st.subheader("Complaints per area")
        mplot(g.set_index("area")["total"], color="#dc2626")
    with t2:
        st.subheader("Reports over time")
        mplot(df.groupby(df.date.str[:10]).size(), kind="line", color="#1c1917")
    st.subheader("Area × category breakdown")
    mplot(df.pivot_table(index="area", columns="category", values="report_id", aggfunc="count", fill_value=0), stacked=True, h=3.6)
    st.subheader("Problem hotspots")
    hot = df.groupby(["area", "category"]).size().reset_index(name="reports").sort_values("reports", ascending=False)
    table(hot[hot.reports >= 2].head(10))
    if df.overdue.any():
        st.subheader("Overdue reports (past SLA)")
        show_table(df[df.overdue])
    st.subheader("Duplicate reports")
    dup = df[df.duplicate_of.notna()]
    if dup.empty:
        st.caption("None detected.")
    else:
        show_table(dup)

    st.subheader("Manage complaints")
    f1, f2 = st.columns(2)
    p = f1.selectbox("Priority", ["All", "High", "Medium", "Low"])
    ar = f2.selectbox("Area", ["All"] + sorted(df.area.unique()))
    v = df if p == "All" else df[df.priority == p]
    show_table(v if ar == "All" else v[v.area == ar])
    c1, c2, c3 = st.columns([1, 2, 1])
    rid = c1.selectbox("Report ID", df.report_id)
    new = c2.selectbox("New status", STATUS)
    if c3.button("Update", width="stretch"):
        set_status(int(rid), new)
        st.success("Status updated.")
        st.rerun()
    st.download_button("Export all reports (CSV)", df.drop(columns=["dt", "overdue"]).to_csv(index=False), "civicpulse_reports.csv")


def page_notes():
    hero("Notifications")
    uid = st.session_state.user["user_id"]
    with db() as c:
        rows = c.execute("SELECT message,date,seen FROM notifications WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
        c.execute("UPDATE notifications SET seen=1 WHERE user_id=?", (uid,))
    if not rows:
        st.info("Nothing yet. You'll be notified when your report is assigned or resolved.")
    for r in rows:
        txt = f"{'NEW · ' if not r['seen'] else ''}{r['message']}  \n*{r['date']}*"
        if "resolved" in r["message"]:
            st.success(txt)
        else:
            st.info(txt)


def page_assign():
    hero("Assign work to workers")
    df, ws = load(), read("SELECT * FROM workers")
    todo = df[df.assigned_to.isna() & df.status.isin(OPEN)]
    todo = todo.sort_values("priority", key=lambda x: x.map({"High": 0, "Medium": 1, "Low": 2}))
    if todo.empty:
        st.success("All open reports are assigned.")
        return
    lab = {r.report_id: f"#{r.report_id} · {r.priority} · {r.category} · {r.area}" for r in todo.itertuples()}
    rid = st.selectbox("Report to assign (High priority first)", list(lab), format_func=lab.get, key="ar")
    row = todo[todo.report_id == rid].iloc[0]
    st.caption(f"“{row.description}”  — reported by {row.username} on {row.date}")
    ws = ws.assign(m=ws.skill != row.category).sort_values("m")
    wl = {w.user_id: f"{w.full_name} · {w.skill} · {w.shift_start}-{w.shift_end}" + ("  skill match" if not w.m else "")
          for w in ws.itertuples()}
    wid = st.selectbox("Assign to worker", list(wl), format_func=wl.get, key="aw")
    c1, c2 = st.columns(2)
    d = c1.date_input("Date", min_value=datetime.now(IST).date())
    t = c2.time_input("Time", value=time(10, 0), step=1800)
    if st.button("Assign & notify citizen"):
        w, sched, hhmm = ws[ws.user_id == wid].iloc[0], f"{d} {t:%H:%M}", f"{t:%H:%M}"
        busy = df[(df.assigned_to == wid) & (df.scheduled == sched) & df.status.isin(OPEN)]
        if not (w.shift_start <= hhmm <= w.shift_end):
            st.error(f"{w.full_name} works {w.shift_start}-{w.shift_end}. Pick a time inside the shift.")
        elif not busy.empty:
            st.error(f"{w.full_name} already has report #{busy.iloc[0].report_id} at that time.")
        else:
            with db() as c:
                c.execute("UPDATE reports SET assigned_to=?, scheduled=? WHERE report_id=?", (int(wid), sched, int(rid)))
            notify(row.user_id, f"Your report #{rid} ({row.category}, {row.area}) is assigned to {w.full_name} "
                                f"({w.phone}). Visit scheduled: {sched}.")
            st.success(f"Assigned to {w.full_name} at {sched}. The citizen has been notified.")
            st.rerun()


def worker_board():
    """Live worker availability: on shift now + not busy = available."""
    df = load()
    ws = read("SELECT * FROM workers")
    hhmm = datetime.now(IST).strftime("%H:%M")

    def state(w):
        if not (w.shift_start <= hhmm <= w.shift_end):
            return "Off shift"
        return "Busy" if ((df.assigned_to == w.user_id) & (df.status == "In Progress")).any() else "Available"

    ws["status_now"] = ws.apply(state, axis=1)
    ws["shift"] = ws.shift_start + " - " + ws.shift_end
    ws["open_tasks"] = [int(((df.assigned_to == i) & df.status.isin(OPEN)).sum()) for i in ws.user_id]
    ws["completed"] = [int(((df.assigned_to == i) & (df.status == "Resolved")).sum()) for i in ws.user_id]
    a, b, c, d = st.columns(4)
    a.metric("Total workers", len(ws))
    b.metric("Available now", int((ws.status_now == "Available").sum()))
    c.metric("Busy", int((ws.status_now == "Busy").sum()))
    d.metric("Off shift", int((ws.status_now == "Off shift").sum()))
    table(ws[["full_name", "skill", "phone", "shift", "status_now", "open_tasks", "completed"]].rename(
        columns={"status_now": "status"}))


def page_workers():
    hero("Workers & schedule")
    df = load()
    ws = read("SELECT w.*, u.username FROM workers w JOIN users u ON u.user_id=w.user_id")
    ws["shift"] = ws.shift_start + " - " + ws.shift_end
    ws["open_tasks"] = [int(((df.assigned_to == i) & df.status.isin(OPEN)).sum()) for i in ws.user_id]
    ws["completed"] = [int(((df.assigned_to == i) & (df.status == "Resolved")).sum()) for i in ws.user_id]
    t1, t2, t3 = st.tabs(["Workers", "Schedule", "Add worker"])
    with t1:
        worker_board()
        mplot(ws.set_index("full_name")[["open_tasks", "completed"]], color=["#dc2626", "#1c1917"])
        st.caption("Demo worker password: worker123")
    with t2:
        sch = df[df.assigned_to.notna()].sort_values("scheduled")
        pick = st.selectbox("Worker", ["All"] + list(ws.full_name))
        sch = sch if pick == "All" else sch[sch.assigned_worker == pick]
        if sch.empty:
            st.info("No work scheduled yet. Use 'Assign work' to schedule a worker.")
        else:
            table(sch[["scheduled", "assigned_worker", "report_id", "category", "area", "priority", "status"]])
    with t3:
        with st.form("nw", clear_on_submit=True):
            a, b = st.columns(2)
            u, p = a.text_input("Username"), b.text_input("Password", type="password")
            n, ph = a.text_input("Full name"), b.text_input("Phone")
            sk = a.selectbox("Skill / department", CATS)
            s1, s2 = st.columns(2)
            st_, en = s1.time_input("Shift start", time(9, 0)), s2.time_input("Shift end", time(17, 0))
            if st.form_submit_button("Add worker"):
                if not (u.strip() and n.strip() and len(p) >= 6):
                    st.error("Fill username, name and a password of 6+ characters.")
                elif add_worker(u, p, n, ph, sk, f"{st_:%H:%M}", f"{en:%H:%M}"):
                    st.success(f"{n} added."); st.rerun()
                else:
                    st.error("That username is taken.")


def page_tasks():
    uid = st.session_state.user["user_id"]
    w = read("SELECT * FROM workers WHERE user_id=?", (uid,)).iloc[0]
    hero(f"My tasks: {w.full_name}")
    st.caption(f"{w.skill} • shift {w.shift_start}-{w.shift_end} • {w.phone}")
    df = load()
    mine = df[df.assigned_to == uid].sort_values("scheduled")
    a, b = st.columns(2)
    a.metric("Open tasks", int(mine.status.isin(OPEN).sum())); b.metric("Completed", int((mine.status == "Resolved").sum()))
    if mine.empty:
        st.info("No work assigned yet.")
    for r in mine.itertuples():
        with st.container(border=True):
            st.markdown(f"**#{r.report_id} · {r.category}** — {escape(r.area)} ({escape(r.location or 'no landmark')}) · {pill(r.priority)}\n\n"
                        f"**{r.scheduled}** · {pill(r.status)}\n\n{escape(r.description)}", unsafe_allow_html=True)
            if isinstance(r.image, str): photo(r.report_id, width=220)
            c1, c2, _ = st.columns([1, 1, 3])
            if r.status == "Pending" and c1.button("Start work", key=f"s{r.report_id}"):
                set_status(r.report_id, "In Progress", w.full_name); st.rerun()
            if r.status in OPEN and c2.button("Mark resolved", key=f"d{r.report_id}"):
                set_status(r.report_id, "Resolved", w.full_name); st.rerun()


def footer():
    st.markdown(f'<div class="brand"><div class="row"><svg width="54" height="54" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><path d="M24 3C15.2 3 8 10.2 8 19c0 12 16 26 16 26s16-14 16-26C40 10.2 32.8 3 24 3z" fill="#dc2626"/><circle cx="24" cy="19" r="11" fill="#ffffff"/><polyline points="15,19 20,19 22,12 26,26 29,19 33,19" fill="none" stroke="#dc2626" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg><span class="name">Civic<b>Pulse</b></span></div>'
                '<div class="tag">Discover unreported local problems</div>'
                '<div class="copy">&copy; 2026 CivicPulse &middot; Built with Python, Streamlit and SQLite</div></div>',
                unsafe_allow_html=True)


# ---------- main
st.set_page_config(page_title="CivicPulse", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
init()
user = st.session_state.get("user")
if not user:
    page_auth()
else:
    role = user["role"]
    if role == "admin":
        pages = {"Dashboard": page_dash, "Assign work": page_assign, "Workers & schedule": page_workers,
                 "Area insights": page_area, "Leaderboard": page_leaders}
    elif role == "worker":
        pages = {"My tasks": page_tasks}
    else:
        pages = {"Report a problem": page_submit, "Community board": page_board, "My reports": page_my,
                 "Notifications": page_notes, "Area insights": page_area, "Leaderboard": page_leaders}
    with db() as c:
        n = c.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND seen=0", (user["user_id"],)).fetchone()[0]
    if st.session_state.pop("welcome", False) and n:
        st.toast(f"You have {n} new notification(s)")
    with st.sidebar:
        st.markdown("## CivicPulse")
        st.markdown(f"**{user['username']}** &nbsp;<span class='pill' style='background:#fff;color:#b91c1c !important'>{role}</span>",
                    unsafe_allow_html=True)
        if st.session_state.get("page") not in pages:
            st.session_state.page = list(pages)[0]
        st.markdown("<div class='navlabel'>MENU</div>", unsafe_allow_html=True)
        for k in pages:
            if st.button(k + (f" ({n})" if "Notif" in k and n else ""), key=f"nav_{k}",
                         type="primary" if k == st.session_state.page else "secondary"):
                st.session_state.page = k
                st.rerun()
        st.divider()
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
    pages[st.session_state.page]()
    footer()
