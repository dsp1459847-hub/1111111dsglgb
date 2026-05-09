import pandas as pd
import streamlit as st
from collections import Counter, defaultdict  # <-- Yeh line error theek karegi

st.set_page_config(layout="wide", page_title="MAYA AI: TIERED DYNAMIC FIXED")

# --- CSS for High-Pro Display ---
st.markdown("""
    <style>
    .compact-grid { display:grid; grid-template-columns: repeat(5, 1fr); gap: 2px; }
    .item-box { font-size: 13px; padding: 4px; text-align: center; border: 1px solid #ddd; border-radius: 2px; font-weight: bold; }
    .shift-header { background: #111; color: #00FF00; text-align: center; font-weight: bold; padding: 5px; border-radius: 5px; border: 1px solid #333; }
    .stTable { font-size: 11px !important; }
    </style>
    """, unsafe_allow_html=True)

def get_val_str(val):
    if pd.isna(val) or str(val).strip() in ["", "XX", "nan"]: return ""
    # Sabhi anko ko 2 digit format me lane ke liye
    v = str(val).replace('.0','').strip()
    return v.zfill(2)[-2:] if v.isdigit() else ""

def apply_32(val_str):
    if not val_str or len(str(val_str)) != 2 or not str(val_str).isdigit(): 
        return set()
    val_str = str(val_str)
    A, B = int(val_str[0]), int(val_str[1])
    PAT = [(0,1),(0,-1),(1,0),(-1,0),(0,5),(0,-5),(5,0),(-5,0),(1,4),(-1,-4),(4,1),(-4,-1),(1,6),(-1,-6),(6,1),(-6,-1),(1,1),(-1,-1),(1,-1),(-1,1),(5,5),(-5,-5),(5,-5),(5,-5),(1,5),(-1,-5),(1,-5),(-1,5),(5,1),(-5,-1),(5,-1),(-5,1)]
    return {f"{(A+da)%10}{(B+db)%10}" for da, db in PAT}

def get_tiered_logic(df, t_date, target_shift):
    # Pichle 1 saal ka data check karna
    hist = df[df['DATE'] < pd.to_datetime(t_date)].tail(365)
    if len(hist) < 60: return set()

    serial_hits = []
    shifts_to_check = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    
    # 1. Full Audit (6 shifts * 60 days)
    for src in shifts_to_check:
        for lb in range(1, 61):
            hits = 0
            # History me loop chala kar check karna ki pattern kitni baar aya
            for i in range(len(hist)-1, 60, -1):
                tgt = get_val_str(hist.iloc[i][target_shift])
                src_v = get_val_str(hist.iloc[i-lb][src])
                if tgt and src_v and tgt in apply_32(src_v):
                    hits += 1
            if hits > 0:
                serial_hits.append(((src, lb), hits))

    if not serial_hits: return set()
    
    # Sorting logic
    serial_hits.sort(key=lambda x: x[1], reverse=True)
    max_h = serial_hits[0][1]
    min_h = serial_hits[-1][1]

    # Dynamic Thresholds (Top 10% and Bottom 10% hierarchy)
    toppers = [x for x in serial_hits if x[1] >= max_h * 0.9]
    losers = [x for x in serial_hits if x[1] <= min_h * 1.1]

    top_pool = set()
    for (src, lb), h in toppers:
        # Target date se thik piche wale lookback anko ko uthana
        val = df[df['DATE'] < pd.to_datetime(t_date)].iloc[-lb][src]
        top_pool.update(apply_32(get_val_str(val)))

    minus_pool = set()
    for (src, lb), h in losers:
        val = df[df['DATE'] < pd.to_datetime(t_date)].iloc[-lb][src]
        minus_pool.update(apply_32(get_val_str(val)))

    # Final Filtered Result
    return top_pool - minus_pool

# --- UI Layout ---
uploaded_file = st.file_uploader("Upload 0DSP0 File", type=['xlsx','csv'], label_visibility="collapsed")

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    shifts = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']

    t_date = st.date_input("Target Date", df['DATE'].max())
    st.write(f"### ⚡ Tiered Dynamic Engine (Fix Mode): {t_date.strftime('%d-%b-%Y')}")

    cols = st.columns(6)
    actual_row = df[df['DATE'] == pd.to_datetime(t_date)]
    
    for i, s_name in enumerate(shifts):
        with cols[i]:
            st.markdown(f"<div class='shift-header'>{s_name}</div>", unsafe_allow_html=True)
            preds = get_tiered_logic(df, t_date, s_name)
            actual = get_val_str(actual_row[s_name].values[0]) if not actual_row.empty else ""
            
            html = "<div class='compact-grid' style='margin-top:5px;'>"
            for p in sorted(list(preds)):
                # Matching green highlight logic
                bg = "#28a745" if p == actual and actual != "" else "#222"
                color = "white" if p == actual else "#aaa"
                html += f"<div class='item-box' style='background:{bg}; color:{color}; border:0.5px solid #444;'>{p}</div>"
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")
    # --- Live Audit History ---
    st.subheader("📜 Live Hierarchy Audit (Top-Tier vs Relative-Loser)")
    hist_view = df[df['DATE'] <= pd.to_datetime(t_date)].tail(11).copy().sort_values('DATE', ascending=False)
    
    audit_list = []
    for _, row in hist_view.iterrows():
        day_res = {"Tarikh": row['DATE'].strftime('%d-%m'), "Bar": row['DATE'].strftime('%a')}
        for s in shifts:
            p_list = get_tiered_logic(df, row['DATE'], s)
            val = get_val_str(row[s])
            day_res[s] = f"✅ {val}" if val in p_list and val != "" else val
        audit_list.append(day_res)
    
    st.table(pd.DataFrame(audit_list))
    
