import streamlit as st
import pandas as pd
import random

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

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("nike_liga_data.csv")
    # Support both column naming conventions
    df.columns = [c.strip() for c in df.columns]
    if "Players" in df.columns:
        df = df.rename(columns={"Players": "Player", "Values": "Value"})
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

    # Score bar visual
    filled = "🟩" * score + "🟥" * (MAX_ROUNDS - score)
    st.markdown(f"<div style='text-align:center;font-size:1.5rem;letter-spacing:4px'>{filled}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Play again"):
        init_state()
        st.rerun()
    st.stop()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align:center;font-size:3rem;margin-bottom:0'>⚽ GUESS MY VALUE</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#8b949e;margin-top:0'>Niké Liga · Season 2025/26</p>", unsafe_allow_html=True)

# Score bar
i0, i1 = st.session_state.indices
st.markdown(f"""
<div class='scorebar'>
    <span>Round <strong>{st.session_state.round}</strong> / {MAX_ROUNDS}</span>
    <span>✅ Score: <strong>{st.session_state.score}</strong></span>
    <span>Remaining: <strong>{MAX_ROUNDS - st.session_state.round + 1}</strong></span>
</div>
""", unsafe_allow_html=True)

# ── Player A card (known value) ────────────────────────────────────────────────
row_a = df.loc[i0]
st.markdown(f"""
<div class='card'>
    <div class='badge'>{'Club: ' + row_a['Club'] if 'Club' in df.columns else 'Niké Liga'}</div>
    <div class='player-name'>{row_a['Player']}</div>
    <div class='player-value'>{fmt_value(row_a['Value'])}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='text-align:center;font-size:1.4rem;color:#8b949e;margin:4px 0'>VS</div>", unsafe_allow_html=True)

# ── Player B card (hidden value) ───────────────────────────────────────────────
row_b = df.loc[i1]
revealed = st.session_state.answered
b_value_display = fmt_value(row_b['Value']) if revealed else "???"
b_value_class = "player-value" if revealed else "player-value-hidden"

st.markdown(f"""
<div class='card'>
    <div class='badge'>{'Club: ' + row_b['Club'] if 'Club' in df.columns else 'Niké Liga'}</div>
    <div class='player-name'>{row_b['Player']}</div>
    <div class='{b_value_class}'>{b_value_display}</div>
</div>
""", unsafe_allow_html=True)

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

# ── Guess buttons ──────────────────────────────────────────────────────────────
else:
    st.markdown(f"<p style='text-align:center;color:#8b949e;margin:16px 0 8px'>Is <strong style='color:#fff'>{row_b['Player']}</strong>'s value HIGHER or LOWER than {fmt_value(row_a['Value'])}?</p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📈 HIGHER", key="higher"):
            handle_guess("higher")
            st.rerun()
    with col2:
        if st.button("📉 LOWER", key="lower"):
            handle_guess("lower")
            st.rerun()

# ── Sidebar: progress ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Your progress")
    st.progress(st.session_state.score / MAX_ROUNDS)
    st.metric("Correct", st.session_state.score)
    st.metric("Accuracy", f"{int(st.session_state.score / st.session_state.round * 100)}%" if st.session_state.round > 0 else "—")
    st.markdown("---")
    if st.button("🔄 Restart game"):
        init_state()
        st.rerun()
    st.markdown("---")
    st.markdown("**How to play**")
    st.markdown("You'll see two Niké Liga players. Guess whether the second player's market value is higher or lower than the first. 10 rounds, aim for a high score!")