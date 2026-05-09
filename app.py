import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide", page_title="MAYA AI: UNIVERSAL AUDITOR")

# --- Custom Styling for Compact Grid & History ---
st.markdown("""
    <style>
    .compact-grid { display:grid; grid-template-columns: repeat(5, 1fr); gap: 2px; }
    .item-box { font-size: 12px; padding: 3px; text-align: center; border: 1px solid #ddd; border-radius: 2px; font-weight: bold; }
    .shift-header { background: #1E1E1E; color: gold; text-align: center; font-weight: bold; padding: 5px; border-radius: 5px; margin-top: 10px; }
    .stTable { font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Logic Configuration (7-yr Audit Constants) ---
CONFIG = {
    'DS': {'top': [('GL', 48), ('GD', 28), ('DS', 53)], 'flop': [('SG', 7), ('DS', 8), ('GD', 8)]},
    'FD': {'top': [('GD', 57), ('DS', 3), ('SG', 39)], 'flop': [('FD', 7), ('FD', 8), ('GL', 8)]},
    'GD': {'top': [('DS', 59), ('DS', 9), ('SG', 51)], 'flop': [('GD', 7), ('GD', 8), ('DB', 8)]},
    'GL': {'top': [('GL', 13), ('GL', 44), ('GD', 28)], 'flop': [('GL', 7), ('GL', 8), ('DS', 8)]},
    'DB': {'top': [('SG', 15), ('FD', 48), ('DB', 50)], 'flop': [('DB', 7), ('DB', 8), ('FD', 8)]},
    'SG': {'top': [('DS', 19), ('SG', 9), ('GL', 8)], 'flop': [('SG', 7), ('SG', 8), ('GL', 7)]}
}

def apply_32(val_str):
    if not val_str or len(val_str) != 2: return set()
    A, B = int(val_str[0]), int(val_str[1])
    PAT = [(0,1),(0,-1),(1,0),(-1,0),(0,5),(0,-5),(5,0),(-5,0),(1,4),(-1,-4),(4,1),(-4,-1),(1,6),(-1,-6),(6,1),(-6,-1),(1,1),(-1,-1),(1,-1),(-1,1),(5,5),(-5,-5),(5,-5),(5,-5),(1,5),(-1,-5),(1,-5),(-1,5),(5,1),(-5,-1),(5,-1),(-5,1)]
    return {f"{(A+da)%10}{(B+db)%10}" for da, db in PAT}

def get_predictions(df, t_date, shift):
    hist = df[df['DATE'] < pd.to_datetime(t_date)]
    if hist.empty: return set()
    cfg = CONFIG.get(shift)
    # Top Pool
    top_pool = set()
    for src, lb in cfg['top']:
        if len(hist) >= lb: top_pool.update(apply_32(hist.iloc[-lb][src]))
    # Minus Pool
    minus_pool = set()
    for src, lb in cfg['flop']:
        if len(hist) >= lb: minus_pool.update(apply_32(hist.iloc[-lb][src]))
    return top_pool - minus_pool

# --- UI Setup ---
uploaded_file = st.file_uploader("Upload 0DSP0 File", type=['xlsx','csv'], label_visibility="collapsed")

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    shifts = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    for s in shifts:
        df[s] = df[s].apply(lambda x: str(x).replace('.0','').strip().zfill(2)[-2:] if pd.notna(x) and str(x).strip() != "" else "")

    t_date = st.date_input("Target Date", df['DATE'].max())
    st.write(f"### 🎯 Universal VIP Prediction: {t_date.strftime('%d-%b-%Y')} ({t_date.strftime('%A')})")

    # Prediction Grid (Current Day)
    actual_row = df[df['DATE'] == pd.to_datetime(t_date)]
    cols = st.columns(6)
    for i, s_name in enumerate(shifts):
        with cols[i]:
            st.markdown(f"<div class='shift-header'>{s_name}</div>", unsafe_allow_html=True)
            preds = get_predictions(df, t_date, s_name)
            actual = actual_row[s_name].values[0] if not actual_row.empty else ""
            
            html = "<div class='compact-grid' style='margin-top:5px;'>"
            for p in sorted(list(preds)):
                bg = "#28a745" if p == actual and actual != "" else "#f0f2f6"
                color = "white" if p == actual else "black"
                html += f"<div class='item-box' style='background:{bg}; color:{color};'>{p}</div>"
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")
    
    # --- 11-Day Live Audit History (Exactly as requested) ---
    st.subheader("📜 11-Day Performance History (Bar & Date wise Audit)")
    # Prediction wale din ko milakar pichle 11 din
    hist_view = df[df['DATE'] <= pd.to_datetime(t_date)].tail(11).copy().sort_values('DATE', ascending=False)
    
    audit_list = []
    for _, row in hist_view.iterrows():
        day_res = {
            "Tarikh": row['DATE'].strftime('%d-%m'),
            "Bar (Day)": row['DATE'].strftime('%a')
        }
        for s in shifts:
            p_list = get_predictions(df, row['DATE'], s)
            val = row[s]
            # Agar us din result prediction mein tha toh green dabba logic yahan text mein dikhega
            day_res[s] = f"🟢 {val}" if val in p_list and val != "" else val
        audit_list.append(day_res)
    
    st.table(pd.DataFrame(audit_list))
    
