import pandas as pd
import streamlit as st
from collections import defaultdict

st.set_page_config(layout="wide", page_title="MAYA AI: GOLDEN QUADRUPLE")

# --- Compact Styling ---
st.markdown("""
    <style>
    .compact-grid { display:grid; grid-template-columns: repeat(5, 1fr); gap: 2px; }
    .item { font-size: 11px; padding: 2px; text-align: center; border: 1px solid #ddd; border-radius: 2px; }
    .header-golden { background: #FF00FF; color: white; text-align: center; font-weight: bold; padding: 2px; border-radius: 4px; }
    .header-triple { background: #FFD700; color: black; text-align: center; font-weight: bold; padding: 2px; border-radius: 4px; }
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

# --- 8 Golden Ank Logic (Backtest Based) ---
def get_golden_8(df, t_date):
    hist = df[df['DATE'] < pd.to_datetime(t_date)].tail(30)
    # Ye wo logic hai jo mahine mein 10 din pass hota hai
    all_vals = []
    for c in ['DS','GL','GD']: all_vals.extend(hist[c].tolist())
    counts = Counter(all_vals)
    return {num for num, count in counts.most_common(8)} # Top 8 repeating anks

# --- Optimized Lookbacks ---
TOP_DAYS = {'DS': [4, 6, 9], 'GL': [3, 4, 8], 'GD': [1, 5, 8]}
FLOP_DAYS = {'DS': [1, 3, 7], 'GL': [7, 10, 5], 'GD': [2, 9, 10]}

def get_quadruple_predictions(df, t_date):
    hist = df[df['DATE'] < pd.to_datetime(t_date)]
    if hist.empty: return set(), set(), set(), set()
    
    # 1. Negative Filter Logic
    pool_ds = set().union(*(apply_32(hist.iloc[-lb]['DS']) for lb in TOP_DAYS['DS'] if len(hist)>=lb))
    pool_gl = set().union(*(apply_32(hist.iloc[-lb]['GL']) for lb in TOP_DAYS['GL'] if len(hist)>=lb))
    pool_gd = set().union(*(apply_32(hist.iloc[-lb]['GD']) for lb in TOP_DAYS['GD'] if len(hist)>=lb))
    
    neg_pool = set()
    for src in FLOP_DAYS:
        for lb in FLOP_DAYS[src]:
            if len(hist)>=lb: neg_pool.update(apply_32(hist.iloc[-lb][src]))
                
    c_ds, c_gl, c_gd = pool_ds - neg_pool, pool_gl - neg_pool, pool_gd - neg_pool
    
    # 2. Basic Triple/Double
    triple = c_ds & c_gl & c_gd
    double = (c_ds & c_gl) | (c_ds & c_gd) | (c_gl & c_gd) - triple
    
    # 3. GOLDEN INTERSECTION (The 4th confirmation)
    golden_8 = get_golden_8(df, t_date)
    golden_top = (triple | double) & golden_8
    
    return golden_top, triple - golden_top, double - golden_top, golden_8

# --- UI Setup ---
uploaded_file = st.file_uploader("Upload 0DSP0 File", type=['xlsx','csv'], label_visibility="collapsed")

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    for c in ['DS','FD','GD','GL','DB','SG']: df[c] = df[c].apply(get_val_str)
    
    t_date = st.date_input("Select Date", df['DATE'].max())
    actual_ds = df[df['DATE'] == pd.to_datetime(t_date)]['DS'].values[0] if not df[df['DATE'] == pd.to_datetime(t_date)].empty else ""

    g_top, triple, double, g8 = get_quadruple_predictions(df, t_date)

    st.write(f"### 🛡️ Quadruple VIP Dashboard: {t_date.strftime('%d-%b')}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='header-golden'>👑 GOLDEN TOP (Matching 8-Ank)</div>", unsafe_allow_html=True)
        html = "<div class='compact-grid'>"
        for n in sorted(list(g_top)):
            bg = "#28a745" if n == actual_ds else "#FFD700"
            html += f"<div class='item' style='background:{bg}; color:black; font-weight:bold;'>{n}</div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='header-triple'>🏆 TRIPLE VIP (Cleaned)</div>", unsafe_allow_html=True)
        html = "<div class='compact-grid'>"
        for n in sorted(list(triple)):
            bg = "#28a745" if n == actual_ds else "#f0f2f6"
            html += f"<div class='item' style='background:{bg};'>{n}</div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    with c3:
        st.markdown("<div style='background:#007bff; color:white; text-align:center; font-weight:bold;'>⭐ DOUBLE MATCH</div>", unsafe_allow_html=True)
        html = "<div class='compact-grid'>"
        for n in sorted(list(double)):
            bg = "#28a745" if n == actual_ds else "#f0f2f6"
            html += f"<div class='item' style='background:{bg};'>{n}</div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")
    # --- 11-Day History ---
    st.subheader("📜 11-Day Bar & Date Audit (Golden Mode)")
    hist_view = df[df['DATE'] <= pd.to_datetime(t_date)].tail(11).copy().sort_values('DATE', ascending=False)
    
    audit_data = []
    for _, row in hist_view.iterrows():
        gt, t, d, g8_list = get_quadruple_predictions(df, row['DATE'])
        val = row['DS']
        status = val
        if val in gt: status = f"👑 {val} (GOLDEN)"
        elif val in t: status = f"🏆 {val} (Triple)"
        elif val in d: status = f"⭐ {val} (Double)"
        
        audit_data.append({"Tarikh": row['DATE'].strftime('%d-%m'), "Bar": row['DATE'].strftime('%A'), "DS Result": status, "GL": row['GL'], "GD": row['GD']})
    
    st.table(pd.DataFrame(audit_data))
            
