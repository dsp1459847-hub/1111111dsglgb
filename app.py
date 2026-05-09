import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide", page_title="MAYA AI: AUDIT PRO")

# --- Custom Styling (Numbers ke size ke hisab se dabbe) ---
st.markdown("""
    <style>
    .compact-grid { display:grid; grid-template-columns: repeat(5, 1fr); gap: 2px; }
    .item-common { background: #FFD700; color: black; font-size: 14px; padding: 4px; text-align: center; border: 1.5px solid gold; border-radius: 3px; font-weight: bold; }
    .item-unique { background: #f0f2f6; color: black; font-size: 13px; padding: 4px; text-align: center; border: 1px solid #ddd; border-radius: 2px; }
    .header-tag { text-align: center; font-weight: bold; padding: 3px; border-radius: 4px; margin-bottom: 5px; }
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

# Lookback Config
TOP_DAYS = {'DS': [4, 6, 9], 'GL': [3, 4, 8], 'GD': [1, 5, 8]}
FLOP_DAYS = {'DS': [1, 3, 7], 'GL': [7, 10, 5], 'GD': [2, 9, 10]}

def get_audit_predictions(df, t_date):
    hist = df[df['DATE'] < pd.to_datetime(t_date)]
    if hist.empty: return set(), set()
    
    # VIP Logic (Minus lagane ke baad)
    p_ds = set().union(*(apply_32(hist.iloc[-lb]['DS']) for lb in TOP_DAYS['DS'] if len(hist)>=lb))
    p_gl = set().union(*(apply_32(hist.iloc[-lb]['GL']) for lb in TOP_DAYS['GL'] if len(hist)>=lb))
    p_gd = set().union(*(apply_32(hist.iloc[-lb]['GD']) for lb in TOP_DAYS['GD'] if len(hist)>=lb))
    neg = set().union(*(apply_32(hist.iloc[-lb][s]) for s, days in FLOP_DAYS.items() for lb in days if len(hist)>=lb))
    
    vip_pool = (p_ds | p_gl | p_gd) - neg
    g8 = get_golden_8(df, t_date)
    
    common = vip_pool.intersection(g8)
    unique = vip_pool.difference(g8)
    return common, unique

# --- UI Setup ---
uploaded_file = st.file_uploader("Upload Excel", type=['xlsx','csv'], label_visibility="collapsed")

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    for c in ['DS','FD','GD','GL','DB','SG']: df[c] = df[c].apply(get_val_str)
    
    t_date = st.date_input("Select Target Date", df['DATE'].max())
    actual_ds = df[df['DATE'] == pd.to_datetime(t_date)]['DS'].values[0] if not df[df['DATE'] == pd.to_datetime(t_date)].empty else ""

    common, unique = get_audit_predictions(df, t_date)

    st.write(f"### 🎯 DS Prediction Dashboard: {t_date.strftime('%d-%b')} ({t_date.strftime('%A')})")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("<div class='header-tag' style='background:gold; color:black;'>🏆 COMMON (VIP + Golden)</div>", unsafe_allow_html=True)
        html = "<div class='compact-grid'>"
        for n in sorted(list(common)):
            bg = "#28a745" if n == actual_ds else "#FFD700"
            html += f"<div class='item-common' style='background:{bg};'>{n}</div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='header-tag' style='background:#007bff; color:white;'>💎 UNIQUE VIP (Support)</div>", unsafe_allow_html=True)
        html = "<div class='compact-grid' style='grid-template-columns: repeat(8, 1fr);'>"
        for n in sorted(list(unique)):
            bg = "#28a745" if n == actual_ds else "#f0f2f6"
            html += f"<div class='item-unique' style='background:{bg};'>{n}</div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")
    # --- 11-Day Bar & Date Audit History ---
    st.subheader("📜 11-Day Performance Audit (Bar + Date wise)")
    hist_view = df[df['DATE'] <= pd.to_datetime(t_date)].tail(11).copy().sort_values('DATE', ascending=False)
    
    audit_data = []
    for _, row in hist_view.iterrows():
        com, uni = get_audit_predictions(df, row['DATE'])
        val = row['DS']
        status = val
        if val in com: status = f"⭐ {val} (Common Hit)"
        elif val in uni: status = f"🟢 {val} (VIP Hit)"
        
        audit_data.append({
            "Tarikh": row['DATE'].strftime('%d-%m'),
            "Bar (Day)": row['DATE'].strftime('%A'),
            "DS Result": status,
            "GL": row['GL'], "GD": row['GD'], "FD": row['FD']
        })
    
    st.table(pd.DataFrame(audit_data))
    
