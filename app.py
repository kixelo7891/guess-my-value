import streamlit as st
import pandas as pd
import random
import sqlite3
from supabase import create_client
import uuid
import re

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Niké Liga – Guess My Value",
    page_icon="⚽",
    layout="centered",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0d1117;
    color: #e6edf3;
}

h1, h2, h3 {
    font-family: 'Bebas Neue', sans-serif;
    letter-spacing: 2px;
}

.card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 16px;
}

.player-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    color: #ffffff;
    letter-spacing: 1.5px;
}

.player-value {
    font-size: 1.4rem;
    color: #3fb950;
    font-weight: 600;
}

.player-value-hidden {
    font-size: 1.4rem;
    color: #8b949e;
    font-weight: 600;
    letter-spacing: 4px;
}

.badge {
    display: inline-block;
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.8rem;
    color: #8b949e;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.result-correct {
    background: #0d2818;
    border: 1px solid #3fb950;
    border-radius: 10px;
    padding: 16px 20px;
    color: #3fb950;
    font-weight: 600;
    font-size: 1.1rem;
}

.result-wrong {
    background: #2d1515;
    border: 1px solid #f85149;
    border-radius: 10px;
    padding: 16px 20px;
    color: #f85149;
    font-weight: 600;
    font-size: 1.1rem;
}

.scorebar {
    background: #21262d;
    border-radius: 8px;
    padding: 12px 20px;
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
    font-size: 0.95rem;
}

div[data-testid="stButton"] button {
    width: 100%;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.2rem;
    letter-spacing: 1.5px;
    border-radius: 8px;
    padding: 10px;
    border: none;
    cursor: pointer;
    transition: opacity 0.15s;
}

div[data-testid="stButton"] button:hover {
    opacity: 0.85;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def track_visit():
    if "visited" not in st.session_state:
        st.session_state.visited = True
        st.session_state.session_id = str(uuid.uuid4())
        try:
            supabase = get_supabase()
            # Insert s unikátnym session_id
            supabase.table("page_views").insert({
                "session_id": st.session_state.session_id
            }).execute()
            # Počítaj všetky riadky a vydel 2
            result = supabase.table("page_views").select("*", count="exact").execute()
            st.session_state.visit_count = result.count // 2
        except Exception as e:
            st.session_state.visit_count = 0
            print(f"Supabase error: {e}")

track_visit()  # ← toto musí byť zavolané

BANNED_WORDS = [
    "kurva", "piča", "jebat", "hovno", "kokot", "debil",
    "cunt", "fuck", "shit", "ass", "retard", "pičovina",
    "čurák", "kunda", "penis", "mušľa", "mušlička", "chuj",
    "jebať", "prijebaný", "prijebaná", "jebavý", "jebavá",
    "pičuš"
]

def is_valid_nickname(nickname: str) -> tuple:
    nick = nickname.strip()
    if len(nick) < 2:
        return False, "Prezývka musí mať aspoň 2 znaky."
    if len(nick) > 20:
        return False, "Prezývka môže mať max 20 znakov."
    if not re.match(r'^[\w\s\-\.]+$', nick):
        return False, "Len písmená, čísla, - _ ."
    for word in BANNED_WORDS:
        if word in nick.lower():
            return False, "Prezývka obsahuje nevhodné slovo."
    return True, ""

def get_unique_nickname(base: str) -> str:
    supabase = get_supabase()
    result = supabase.table("leaderboard")\
        .select("nickname")\
        .like("nickname", f"{base}%")\
        .execute()
    existing = [r["nickname"] for r in result.data]
    if base not in existing:
        return base
    counter = 2
    while f"{base}#{counter}" in existing:
        counter += 1
    return f"{base}#{counter}"

def save_score(nickname: str, score: int, accuracy: int):
    supabase = get_supabase()
    unique_nick = get_unique_nickname(nickname.strip())
    supabase.table("leaderboard").insert({
        "nickname": unique_nick,
        "score": score,
        "accuracy": accuracy
    }).execute()
    return unique_nick

def get_leaderboard():
    supabase = get_supabase()
    result = supabase.table("leaderboard")\
        .select("nickname, score, accuracy, played_at")\
        .order("score", desc=True)\
        .order("accuracy", desc=True)\
        .limit(10)\
        .execute()
    return result.data

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    conn = sqlite3.connect("nike_liga.db")
    df = pd.read_sql("SELECT name AS Player, value AS Value, club AS Club, logo_url AS Logo, player_img_url AS PlayerImg FROM players", conn)
    conn.close()
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df.dropna(subset=["Value"])
    df["Value"] = df["Value"].astype(int)
    return df.reset_index(drop=True)

df = load_data()

MAX_ROUNDS = 10

# ── Session state init ─────────────────────────────────────────────────────────
def init_state():
    st.session_state.round = 1
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.last_correct = None
    st.session_state.game_over = False
    st.session_state.score_saved = False      # ← pridaj
    st.session_state.saved_nickname = ""      # ← pridaj
    for _ in range(100):
        i0, i1 = random.sample(range(len(df)), 2)
        if df.loc[i0, "Value"] != df.loc[i1, "Value"]:
            st.session_state.indices = [i0, i1]
            break

if "round" not in st.session_state:
    init_state()

# ── Helper ─────────────────────────────────────────────────────────────────────
def fmt_value(v: int) -> str:
    if v >= 1_000_000:
        return f"€{v/1_000_000:.2f}m".rstrip("0").rstrip(".")+"m" if not f"€{v/1_000_000:.2f}m".endswith("0m") else f"€{v/1_000_000:.1f}m"
    return f"€{v//1_000}k"

def pick_new_pair():
    for _ in range(100):  # safety limit
        i0, i1 = random.sample(range(len(df)), 2)
        if df.loc[i0, "Value"] != df.loc[i1, "Value"]:
            st.session_state.indices = [i0, i1]
            break
    st.session_state.answered = False
    st.session_state.last_correct = None

def handle_guess(guess: str):
    if st.session_state.answered:
        return

    i0, i1 = st.session_state.indices
    v0 = df.loc[i0, "Value"]
    v1 = df.loc[i1, "Value"]

    correct = (guess == "higher" and v1 > v0) or (guess == "lower" and v1 < v0)
    st.session_state.answered = True
    st.session_state.last_correct = correct
    if correct:
        st.session_state.score += 1

def next_round():
    if st.session_state.round >= MAX_ROUNDS:
        st.session_state.game_over = True
    else:
        st.session_state.round += 1
        pick_new_pair()

# ── Game over screen ───────────────────────────────────────────────────────────
# ── Game over screen ───────────────────────────────────────────────────────────
if st.session_state.game_over:
    score = st.session_state.score
    pct = score * 10

    st.markdown("<h1 style='text-align:center;font-size:3rem'>GAME OVER</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center;color:#8b949e'>Final score: {score}/{MAX_ROUNDS}</h2>", unsafe_allow_html=True)

    if score > 8:
        msg = "🏆 Excellent! You're a master of Niké Liga!"
        color = "#3fb950"
    elif score >= 5:
        msg = "👍 Not great, not terrible."
        color = "#e3b341"
    else:
        msg = "📺 You should watch more 'Bavme sa o lige.' magazine..."
        color = "#f85149"

    st.markdown(f"""
    <div style='text-align:center;margin:30px 0'>
        <div style='font-size:4rem;font-family:Bebas Neue,sans-serif;color:{color}'>{pct}%</div>
        <div style='font-size:1.2rem;margin-top:8px;color:#e6edf3'>{msg}</div>
    </div>
    """, unsafe_allow_html=True)

    filled = "🟩" * score + "🟥" * (MAX_ROUNDS - score)
    st.markdown(f"<div style='text-align:center;font-size:1.5rem;letter-spacing:4px'>{filled}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Nickname input ─────────────────────────────────────────────────────────
    if not st.session_state.get("score_saved", False):
        st.markdown("<h3 style='text-align:center'>🏅 Ulož svoje skóre</h3>", unsafe_allow_html=True)
        nickname = st.text_input("Zadaj prezývku:", max_chars=20, placeholder="napr. SlovanFan99")
        if st.button("💾 Uložiť skóre", use_container_width=True):
            if nickname.strip():
                valid, error_msg = is_valid_nickname(nickname)
                if valid:
                    accuracy = int(score / MAX_ROUNDS * 100)
                    saved_nick = save_score(nickname, score, accuracy)
                    st.session_state.score_saved = True
                    st.session_state.saved_nickname = saved_nick
                    st.rerun()
                else:
                    st.error(error_msg)
            else:
                st.error("Zadaj prezývku.")
    else:
        st.success(f"✅ Skóre uložené ako **{st.session_state.saved_nickname}**!")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Leaderboard ────────────────────────────────────────────────────────────
    st.markdown("<h3 style='text-align:center'>🏆 Top 10 Leaderboard</h3>", unsafe_allow_html=True)
    leaders = get_leaderboard()
    if leaders:
        for i, entry in enumerate(leaders):
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
            is_me = entry["nickname"] == st.session_state.get("saved_nickname", "")
            bg = "#0d2818" if is_me else "#161b22"
            border = "#3fb950" if is_me else "#30363d"
            st.markdown(f"""
            <div style='background:{bg};border:1px solid {border};border-radius:8px;
                        padding:10px 16px;margin-bottom:6px;
                        display:flex;justify-content:space-between;align-items:center'>
                <span>{medal} <strong style='color:#fff'>{entry["nickname"]}</strong></span>
                <span style='color:#3fb950;font-weight:600'>{entry["score"]}/10</span>
                <span style='color:#8b949e'>{entry["accuracy"]}%</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<p style='text-align:center;color:#8b949e'>Zatiaľ žiadne skóre.</p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Hrať znova", use_container_width=True):
        init_state()
        st.rerun()
    st.stop()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align:center;font-size:3rem;margin-bottom:0'>⚽ GUESS MY VALUE</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center;margin:4px 0 20px 0'>
    <svg viewBox="0 0 300 80" width="220" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="og" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style="stop-color:#f97316"/>
                <stop offset="100%" style="stop-color:#ea580c"/>
            </linearGradient>
        </defs>
        <text x="150" y="38" text-anchor="middle"
              font-family="Georgia, serif" font-style="italic" font-weight="700"
              font-size="36" fill="#ffffff" letter-spacing="-1">niké</text>
        <text x="150" y="72" text-anchor="middle"
              font-family="Arial Rounded MT Bold, Nunito, Varela Round, sans-serif"
              font-style="italic" font-weight="900"
              font-size="38" fill="url(#og)" letter-spacing="4"
              stroke="url(#og)" stroke-width="0.5" stroke-linejoin="round">LIGA</text>
    </svg>
    <div style='font-size:0.72rem;color:#8b949e;letter-spacing:3px;margin-top:-4px'>SEASON 2025/26</div>
</div>
""", unsafe_allow_html=True)

# Score bar
i0, i1 = st.session_state.indices
st.markdown(f"""
<div class='scorebar'>
    <span>Round <strong>{st.session_state.round}</strong> / {MAX_ROUNDS}</span>
    <span>✅ Score: <strong>{st.session_state.score}</strong></span>
    <span>Remaining: <strong>{MAX_ROUNDS - st.session_state.round + 1}</strong></span>
</div>
""", unsafe_allow_html=True)

# ── Player A card (known value)
row_a = df.loc[i0]
st.markdown(f"""
<div class="card" style="display:flex;align-items:center;justify-content:space-between;gap:16px">
    <div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
            <img src="{row_a["Logo"]}" width="28" height="28" style="object-fit:contain" onerror="this.style.display='none'">
            <span class="badge" style="margin-bottom:0">{row_a["Club"]}</span>
        </div>
        <div class="player-name">{row_a["Player"]}</div>
        <div style="font-size:0.85rem;color:#8b949e;margin-bottom:4px">MARKET VALUE</div>
        <div class="player-value">{fmt_value(row_a["Value"])}</div>
    </div>
    <img src="{row_a["PlayerImg"]}" width="100" height="120"
     style="border-radius:10px;object-fit:contain;object-position:center;opacity:0.5;flex-shrink:0;background:#21262d"
     onerror="this.style.display='none'">
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='text-align:center;font-size:1.4rem;color:#8b949e;margin:4px 0'>VS</div>", unsafe_allow_html=True)

# ── Player B card (hidden value) ───────────────────────────────────────────────
row_b = df.loc[i1]
revealed = st.session_state.answered
b_value_display = fmt_value(row_b['Value']) if revealed else "? ? ?"
b_value_class = "player-value" if revealed else "player-value-hidden"

st.markdown(f"""
<div class="card" style="display:flex;align-items:center;justify-content:space-between;gap:16px">
    <div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
            <img src="{row_b["Logo"]}" width="28" height="28" style="object-fit:contain" onerror="this.style.display='none'">
            <span class="badge" style="margin-bottom:0">{row_b["Club"]}</span>
        </div>
        <div class="player-name">{row_b["Player"]}</div>
        <div style="font-size:0.85rem;color:#8b949e;margin-bottom:4px">MARKET VALUE</div>
        <div class="{b_value_class}">{b_value_display}</div>
    </div>
    <img src="{row_b["PlayerImg"]}" width="100" height="120"
         style="border-radius:10px;object-fit:cover;object-position:center;opacity:0.5;flex-shrink:0;background:#21262d"
         onerror="this.style.display='none'">
</div>
""", unsafe_allow_html=True)


# ── HIGHER / LOWER tlačidlá priamo pod Player B kartičkou ─────────────────────
if not st.session_state.answered:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📈 HIGHER", key="higher", use_container_width=True):
            handle_guess("higher")
            st.rerun()
    with col2:
        if st.button("📉 LOWER", key="lower", use_container_width=True):
            handle_guess("lower")
            st.rerun()


# ── Result message ─────────────────────────────────────────────────────────────
if st.session_state.answered:
    if st.session_state.last_correct:
        st.markdown(f"<div class='result-correct'>✅ Correct! {row_b['Player']} is worth {fmt_value(row_b['Value'])}.</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='result-wrong'>❌ Wrong! {row_b['Player']} is worth {fmt_value(row_b['Value'])}.</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    label = "Next round ➡️" if st.session_state.round < MAX_ROUNDS else "See results 🏆"
    if st.button(label):
        next_round()
        st.rerun()

# ── Sidebar: progress ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Your progress")
    st.progress(st.session_state.score / MAX_ROUNDS)
    st.metric("Correct", st.session_state.score)
    st.metric("Accuracy", f"{int(st.session_state.score / st.session_state.round * 100)}%" if st.session_state.round > 0 else "—")
    st.markdown("---")
    views = st.session_state.get("visit_count", 0)
    st.metric("👁️ Total visits", f"{views:,}")
    st.markdown("---")
    if st.button("🔄 Restart game"):
        init_state()
        st.rerun()
    st.markdown("---")
    st.markdown("**How to play**")
    st.markdown("You'll see two Niké Liga players. Guess whether the second player's market value is higher or lower than the first. 10 rounds, aim for a high score!")