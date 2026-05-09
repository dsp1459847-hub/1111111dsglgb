import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide", page_title="MAYA AI: NO-MINUS DASHBOARD")

# --- Compact Styling ---
st.markdown("""
    <style>
    .compact-grid { display:grid; grid-template-columns: repeat(5, 1fr); gap: 2px; }
    .item-top { background: #FFD700; color: black; font-size: 14px; padding: 4px; text-align: center; border: 2px solid #FF4B4B; border-radius: 4px; font-weight: bold; }
    .item-normal { background: #f0f2f6; color: black; font-size: 13px; padding: 4px; text-align: center; border: 1px solid #ddd; border-radius: 2px; }
    .header-label { background: #1E1E1E; color: gold; text-align: center; font-weight: bold; padding: 4px; border-radius: 4px; margin-top: 10px;}
    </style>
    """, unsafe_allow_html=True)

def get_val_str(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip()
    return v.zfill(2)[-2:] if v.isdigit() else ""

def apply_32(val_str):
    if not val_str or len(val_str) != 2: return set()
    A, B = int(val_str[0]), int(val_str[1])
    PAT = [(0,1),(0,-1),(1,0),(-1,0),(0,5),(0,-5),(5,0),(-5,0),(1,4),(-1,-4),(4,1),(-4,-1),(1,6),(-1,-6),(6,1),(-6,-1),(1,1),(-1,-1),(1,-1),(-1,1),(5,5),(-5,-5),(5,-5),(5,-5),(1,5),(-1,-5),(1,-5),(-1,5),(5,1),(-5,-1),(5,-1),(-5,1)]
    return {f"{(A+da)%10}{(B+db)%10}" for da, db in PAT}

def get_golden_8(df, t_date):
    hist = df[df['DATE'] < pd.to_datetime(t_date)].tail(30)
    all_vals = []
    for c in ['DS','GL','GD']: 
        vals = [x for x in hist[c].tolist() if x and x != "XX"]
        all_vals.extend(vals)
    counts = Counter(all_vals)
    return {num for num, count in counts.most_common(8)}

# Lookback Configuration
DAYS_CONFIG = {'DS': [4, 6, 9, 5, 8], 'GL': [3, 4, 8, 1, 2], 'GD': [1, 5, 8, 3, 7]}

def get_no_minus_predictions(df, t_date):
    hist = df[df['DATE'] < pd.to_datetime(t_date)]
    if hist.empty: return set(), set()
    
    # Saare anko ka pool banana (Koi Minus nahi)
    full_pool = set()
    for src, days in DAYS_CONFIG.items():
        for lb in days:
            if len(hist) >= lb:
                full_pool.update(apply_32(hist.iloc[-lb][src]))
    
    g8 = get_golden_8(df, t_date)
    
    # Priority Separation
    top_match = full_pool.intersection(g8)
    remaining = full_pool.difference(g8)
    
    return top_match, remaining

# --- UI Setup ---
uploaded_file = st.file_uploader("Upload File", type=['xlsx','csv'], label_visibility="collapsed")

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    for c in ['DS','FD','GD','GL','DB','SG']: df[c] = df[c].apply(get_val_str)
    
    t_date = st.date_input("Target Date", df['DATE'].max())
    actual_ds = df[df['DATE'] == pd.to_datetime(t_date)]['DS'].values[0] if not df[df['DATE'] == pd.to_datetime(t_date)].empty else ""

    top_ank, rest_ank = get_no_minus_predictions(df, t_date)

    st.write(f"### 🎯 DS Dashboard: {t_date.strftime('%d-%b')} ({t_date.strftime('%A')})")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("<div class='header-label'>👑 TOP MATCH (Golden 8)</div>", unsafe_allow_html=True)
        html = "<div class='compact-grid'>"
        for n in sorted(list(top_ank)):
            bg = "#28a745" if n == actual_ds else "#FFD700"
            html += f"<div class='item-top' style='background:{bg};'>{n}</div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='header-label'>💎 SUPPORT POOL (All Patterns)</div>", unsafe_allow_html=True)
        html = "<div class='compact-grid' style='grid-template-columns: repeat(10, 1fr);'>"
        for n in sorted(list(rest_ank)):
            bg = "#28a745" if n == actual_ds else "#f0f2f6"
            html += f"<div class='item-normal' style='background:{bg};'>{n}</div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")
    # --- 11-Day History (Correct Bar + Date) ---
    st.subheader("📜 11-Day Live Audit (No-Minus Mode)")
    hist_view = df[df['DATE'] <= pd.to_datetime(t_date)].tail(11).copy().sort_values('DATE', ascending=False)
    
    audit_data = []
    for _, row in hist_view.iterrows():
        top, rest = get_no_minus_predictions(df, row['DATE'])
        val = row['DS']
        status = val
        if val in top: status = f"⭐ {val} (TOP HIT)"
        elif val in rest: status = f"✅ {val} (Pool Hit)"
        
        audit_data.append({
            "Tarikh": row['DATE'].strftime('%d-%m'),
            "Bar": row['DATE'].strftime('%A'),
            "DS Result": status,
            "GL": row['GL'], "GD": row['GD'], "FD": row['FD']
        })
    st.table(pd.DataFrame(audit_data))
    
