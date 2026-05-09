import pandas as pd
import streamlit as st
from collections import defaultdict

# Page Config
st.set_page_config(layout="wide", page_title="MAYA AI TURBO")

# --- CSS for Speed & Layout ---
st.markdown("""
    <style>
    .compact-grid { display:grid; grid-template-columns: repeat(5, 1fr); gap: 2px; }
    .item-box { font-size: 12px; padding: 3px; text-align: center; border: 1px solid #ddd; border-radius: 2px; font-weight: bold; }
    .shift-header { background: #1E1E1E; color: gold; text-align: center; font-weight: bold; padding: 5px; border-radius: 5px; }
    .result-box { background: #E1F5FE; color: #01579B; text-align: center; font-size: 14px; font-weight: bold; padding: 5px; margin-top: 5px; border-radius: 5px; border: 1px dashed #01579B; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data # Speed badhane ke liye cache use kiya
def clean_val(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip().upper()
    if v in ["XX", "X", "NAN", "", "NONE"]: return ""
    v_clean = "".join(filter(str.isdigit, v))
    return v_clean.zfill(2)[-2:] if v_clean else ""

# 32 Patterns pre-calculated for speed
PAT = [(0,1),(0,-1),(1,0),(-1,0),(0,5),(0,-5),(5,0),(-5,0),(1,4),(-1,-4),(4,1),(-4,-1),(1,6),(-1,-6),(6,1),(-6,-1),(1,1),(-1,-1),(1,-1),(-1,1),(5,5),(-5,-5),(5,-5),(5,-5),(1,5),(-1,-5),(1,-5),(-1,5),(5,1),(-5,-1),(5,-1),(-5,1)]

def apply_32(v):
    if not v or len(v) != 2: return set()
    A, B = int(v[0]), int(v[1])
    return {f"{(A+da)%10}{(B+db)%10}" for da, db in PAT}

@st.cache_data
def get_turbo_prediction(df_json, t_date, target_shift):
    df = pd.read_json(df_json)
    hist = df[df['DATE'] < pd.to_datetime(t_date)].tail(365)
    if len(hist) < 61: return set()

    all_shifts = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    serial_hits = []

    # Optimization: Pattern match only top lookbacks
    for src in all_shifts:
        for lb in range(1, 61):
            hits = 0
            # Step size 2 for faster audit without losing much accuracy
            for i in range(len(hist)-1, 60, -4): 
                tgt = clean_val(hist.iloc[i][target_shift])
                prev = clean_val(hist.iloc[i-lb][src])
                if tgt and prev and tgt in apply_32(prev): hits += 1
            if hits > 0: serial_hits.append(((src, lb), hits))

    if not serial_hits: return set()
    serial_hits.sort(key=lambda x: x[1], reverse=True)
    
    top_pool = set()
    for (src, lb), h in serial_hits[:4]:
        val = clean_val(df[df['DATE'] < pd.to_datetime(t_date)].iloc[-lb][src])
        top_pool.update(apply_32(val))

    minus_pool = set()
    for (src, lb), h in serial_hits[-7:]:
        val = clean_val(df[df['DATE'] < pd.to_datetime(t_date)].iloc[-lb][src])
        minus_pool.update(apply_32(val))

    return top_pool - minus_pool

# --- UI Setup ---
uploaded_file = st.file_uploader("Upload 0DSP0 File", type=['xlsx','csv'], label_visibility="collapsed")

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    df_json = df.to_json() # For caching
    
    shifts = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    t_date = st.date_input("Target Date", df['DATE'].max())

    st.write(f"### ⚡ MAYA TURBO DASHBOARD")

    cols = st.columns(6)
    actual_row = df[df['DATE'] == pd.to_datetime(t_date)]

    for i, s_name in enumerate(shifts):
        with cols[i]:
            st.markdown(f"<div class='shift-header'>{s_name}</div>", unsafe_allow_html=True)
            
            # Prediction
            preds = get_turbo_prediction(df_json, t_date, s_name)
            
            # History/Result (Bagal mein ya niche)
            actual = clean_val(actual_row[s_name].values[0]) if not actual_row.empty else "Waiting"
            st.markdown(f"<div class='result-box'>Result: {actual if actual else '--'}</div>", unsafe_allow_html=True)
            
            html = "<div class='compact-grid' style='margin-top:5px;'>"
            for p in sorted(list(preds)):
                bg = "#28a745" if p == actual and actual != "" else "#222"
                color = "white" if p == actual else "#aaa"
                html += f"<div class='item-box' style='background:{bg}; color:{color}; border: 1px solid #333;'>{p}</div>"
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")
    # Audit Table
    st.subheader("📜 11-Day Live Audit (Fast View)")
    hist_view = df[df['DATE'] <= pd.to_datetime(t_date)].tail(11).copy().sort_values('DATE', ascending=False)
    
    audit_list = []
    for _, row in hist_view.iterrows():
        day_res = {"Date": row['DATE'].strftime('%d-%m'), "Day": row['DATE'].strftime('%a')}
        for s in shifts:
            p_list = get_turbo_prediction(df_json, row['DATE'], s)
            val = clean_val(row[s])
            day_res[s] = f"✅ {val}" if val in p_list and val != "" else val
        audit_list.append(day_res)
    
    st.table(pd.DataFrame(audit_list))
    
