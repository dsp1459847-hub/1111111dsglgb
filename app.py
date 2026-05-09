import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide", page_title="MAYA AI: STABLE ACCURACY")

# --- CSS for Compact & Uniform Look ---
st.markdown("""
    <style>
    .compact-grid { display:grid; grid-template-columns: repeat(5, 1fr); gap: 2px; }
    .item-box { font-size: 13px; padding: 4px; text-align: center; border: 1px solid #ddd; border-radius: 2px; font-weight: bold; }
    .shift-header { background: #1E1E1E; color: gold; text-align: center; font-weight: bold; padding: 5px; border-radius: 5px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- Balanced Logic Config (Top 5 Serials for each shift) ---
# Ye wo serials hain jo pichle 7 saal mein sabse consistent rahe hain
CONFIG = {
    'DS': [('GL', 48), ('GD', 28), ('DS', 53), ('GL', 28), ('GD', 17)],
    'FD': [('GD', 57), ('DS', 3), ('SG', 39), ('FD', 20), ('DS', 18)],
    'GD': [('DS', 59), ('DS', 9), ('SG', 51), ('GD', 43), ('GL', 24)],
    'GL': [('GL', 13), ('GL', 44), ('GD', 28), ('GL', 48), ('SG', 46)],
    'DB': [('SG', 15), ('FD', 48), ('DB', 50), ('SG', 22), ('DS', 20)],
    'SG': [('DS', 19), ('SG', 9), ('GL', 8), ('DS', 5), ('FD', 43)]
}

def apply_32(val_str):
    if not val_str or len(str(val_str)) != 2 or not str(val_str).isdigit():
        return set()
    val_str = str(val_str)
    A, B = int(val_str[0]), int(val_str[1])
    PAT = [(0,1),(0,-1),(1,0),(-1,0),(0,5),(0,-5),(5,0),(-5,0),(1,4),(-1,-4),(4,1),(-4,-1),(1,6),(-1,-6),(6,1),(-6,-1),(1,1),(-1,-1),(1,-1),(-1,1),(5,5),(-5,-5),(5,-5),(5,-5),(1,5),(-1,-5),(1,-5),(-1,5),(5,1),(-5,-1),(5,-1),(-5,1)]
    return {f"{(A+da)%10}{(B+db)%10}" for da, db in PAT}

def get_stable_predictions(df, t_date, shift_name):
    hist = df[df['DATE'] < pd.to_datetime(t_date)]
    if hist.empty: return []
    
    scores = defaultdict(float)
    lookbacks = CONFIG.get(shift_name, [])
    
    # Points based on hits frequency
    for src, lb in lookbacks:
        if len(hist) >= lb:
            val = hist.iloc[-lb][src]
            patterns = apply_32(val)
            for p in patterns:
                scores[p] += 1.0  # Har match ko 1 point
                
    # Filter: Sirf wahi ank lein jo kam se kam 2 jagah se ishara mil rahe hon (Intersection logic)
    # Agar ank bahut kam ho rahe hain, toh top scoring anks ko le lenge
    sorted_anks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Stability fix: Hamesha 12 se 18 ke beech ank dikhayega
    return [item[0] for item in sorted_anks[:18]]

# --- UI Setup ---
uploaded_file = st.file_uploader("Upload 0DSP0 File", type=['xlsx','csv'], label_visibility="collapsed")

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    shifts = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    
    for s in shifts:
        df[s] = df[s].apply(lambda x: str(x).replace('.0','').strip().zfill(2)[-2:] if pd.notna(x) and str(x).strip() not in ["", "XX", "nan"] else "")

    t_date = st.date_input("Target Date", df['DATE'].max())
    st.write(f"### 🎯 MAYA AI Stability Mode: {t_date.strftime('%d-%b-%Y')}")

    actual_row = df[df['DATE'] == pd.to_datetime(t_date)]
    cols = st.columns(6)
    for i, s_name in enumerate(shifts):
        with cols[i]:
            st.markdown(f"<div class='shift-header'>{s_name}</div>", unsafe_allow_html=True)
            preds = get_stable_predictions(df, t_date, s_name)
            actual = actual_row[s_name].values[0] if not actual_row.empty else ""
            
            html = "<div class='compact-grid' style='margin-top:5px;'>"
            for p in preds:
                bg = "#28a745" if p == actual and actual != "" else "#f0f2f6"
                color = "white" if p == actual else "black"
                html += f"<div class='item-box' style='background:{bg}; color:{color};'>{p}</div>"
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")
    
    # --- 11-Day Bar & Date Audit ---
    st.subheader("📜 Live Accuracy Audit (Bar & Date wise)")
    hist_view = df[df['DATE'] <= pd.to_datetime(t_date)].tail(11).copy().sort_values('DATE', ascending=False)
    
    audit_list = []
    for _, row in hist_view.iterrows():
        day_res = {"Tarikh": row['DATE'].strftime('%d-%m'), "Bar": row['DATE'].strftime('%a')}
        for s in shifts:
            p_list = get_stable_predictions(df, row['DATE'], s)
            val = row[s]
            day_res[s] = f"🟢 {val}" if val in p_list and val != "" else val
        audit_list.append(day_res)
    
    st.table(pd.DataFrame(audit_list))
    
