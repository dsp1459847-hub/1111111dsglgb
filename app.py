import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

# Page Configuration
st.set_page_config(layout="wide", page_title="MAYA AI: CROSS-LINK MASTER")

# --- CSS for Professional Look ---
st.markdown("""
    <style>
    .compact-grid { display:grid; grid-template-columns: repeat(5, 1fr); gap: 2px; }
    .item-box { font-size: 12px; padding: 4px; text-align: center; border: 1px solid #ddd; border-radius: 2px; font-weight: bold; }
    .shift-header { background: #111; color: #00FF00; text-align: center; font-weight: bold; padding: 6px; border-radius: 5px; border: 1px solid #333; margin-bottom: 8px; }
    .stTable { font-size: 11px !important; }
    </style>
    """, unsafe_allow_html=True)

def clean_val(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip().upper()
    if v in ["XX", "X", "NAN", "", "NONE"]: return ""
    v_clean = "".join(filter(str.isdigit, v))
    return v_clean.zfill(2)[-2:] if v_clean else ""

def apply_32(val_str):
    v = clean_val(val_str)
    if not v or len(v) != 2: return set()
    try:
        A, B = int(v[0]), int(v[1])
        PAT = [(0,1),(0,-1),(1,0),(-1,0),(0,5),(0,-5),(5,0),(-5,0),(1,4),(-1,-4),(4,1),(-4,-1),(1,6),(-1,-6),(6,1),(-6,-1),(1,1),(-1,-1),(1,-1),(-1,1),(5,5),(-5,-5),(5,-5),(5,-5),(1,5),(-1,-5),(1,-5),(-1,5),(5,1),(-5,-1),(5,-1),(-5,1)]
        return {f"{(A+da)%10}{(B+db)%10}" for da, db in PAT}
    except:
        return set()

def get_cross_link_prediction(df, t_date, target_shift):
    """हर शिफ्ट के लिए सभी 6 शिफ्टों का ऑडिट (60 दिन लुकबैक)"""
    hist = df[df['DATE'] < pd.to_datetime(t_date)].tail(365)
    if len(hist) < 61: return set()

    all_shifts = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    serial_hits = []

    # 1. ऑडिट: सभी शिफ्टों के 60 दिनों का टेस्ट
    for src in all_shifts:
        for lb in range(1, 61):
            hits = 0
            # पिछले 1 साल के डेटा पर टेस्टिंग
            for i in range(len(hist)-1, 60, -1):
                tgt = clean_val(hist.iloc[i][target_shift])
                prev = clean_val(hist.iloc[i-lb][src])
                if tgt and prev and tgt in apply_32(prev):
                    hits += 1
            if hits > 0:
                serial_hits.append(((src, lb), hits))

    if not serial_hits: return set()

    # 2. सिलेक्शन: Top 4 Hitters और 7 Flop (Minus) Losers
    serial_hits.sort(key=lambda x: x[1], reverse=True)
    
    # टॉप 4 हिट वाले सीरियल
    toppers = serial_hits[:4]
    # सबसे कम 7 हिट वाले सीरियल (Losers)
    losers = serial_hits[-7:]

    target_hist = df[df['DATE'] < pd.to_datetime(t_date)]
    
    top_pool = set()
    for (src, lb), h in toppers:
        val = clean_val(target_hist.iloc[-lb][src])
        top_pool.update(apply_32(val))

    minus_pool = set()
    for (src, lb), h in losers:
        val = clean_val(target_hist.iloc[-lb][src])
        minus_pool.update(apply_32(val))

    # 3. फाइनल माइनस: टॉप में से 7 लूज़र्स को घटाना
    return top_pool - minus_pool

# --- मुख्य प्रोग्राम ---
uploaded_file = st.file_uploader("Upload 0DSP0 File", type=['xlsx','csv'], label_visibility="collapsed")

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    
    shifts = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    t_date = st.date_input("Target Date", df['DATE'].max())

    st.write(f"### 🚀 Maya AI: Cross-Link Master Engine (All-Shift Linked)")
    st.write(f"**Target:** {t_date.strftime('%d-%m-%Y')} | **Strategy:** 4 Top vs 7 Minus")

    # 6 शिफ्टों का ग्रिड
    cols = st.columns(6)
    actual_row = df[df['DATE'] == pd.to_datetime(t_date)]

    for i, s_name in enumerate(shifts):
        with cols[i]:
            st.markdown(f"<div class='shift-header'>{s_name}</div>", unsafe_allow_html=True)
            preds = get_cross_link_prediction(df, t_date, s_name)
            actual = clean_val(actual_row[s_name].values[0]) if not actual_row.empty else ""
            
            html = "<div class='compact-grid'>"
            for p in sorted(list(preds)):
                bg = "#28a745" if p == actual and actual != "" else "#222"
                color = "white" if p == actual else "#aaa"
                html += f"<div class='item-box' style='background:{bg}; color:{color}; border: 1px solid #333;'>{p}</div>"
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")
    
    # 11-दिन का लाइव ऑडिट (हर शिफ्ट की प्रेडिक्शन चेक करने के लिए)
    st.subheader("📜 11-Day Cross-Link Audit History (Green = Pass)")
    hist_view = df[df['DATE'] <= pd.to_datetime(t_date)].tail(11).copy().sort_values('DATE', ascending=False)
    
    audit_list = []
    for _, row in hist_view.iterrows():
        day_res = {"Date": row['DATE'].strftime('%d-%m'), "Day": row['DATE'].strftime('%a')}
        for s in shifts:
            p_list = get_cross_link_prediction(df, row['DATE'], s)
            val = clean_val(row[s])
            day_res[s] = f"✅ {val}" if val in p_list and val != "" else val
        audit_list.append(day_res)
    
    st.table(pd.DataFrame(audit_list))
    
