import pandas as pd
import streamlit as st
from collections import defaultdict

st.set_page_config(layout="wide", page_title="MAYA AI: ALL-PAIR VIP")

# --- Compact CSS ---
st.markdown("""
    <style>
    .compact-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 2px; }
    .item { font-size: 11px; padding: 2px; text-align: center; border: 1px solid #ddd; border-radius: 2px; }
    .tag-common { background: #FFD700; color: black; font-weight: bold; text-align: center; font-size: 12px; }
    .tag-pair { background: #007bff; color: white; font-weight: bold; text-align: center; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

def get_val_str(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip()
    return v.zfill(2)[-2:] if v.isdigit() else ""

def apply_32(val_str):
    if not val_str or len(val_str) != 2: return set()
    A, B = int(val_str[0]), int(val_str[1])
    PAT = [(0,1),(0,-1),(1,0),(-1,0),(0,5),(0,-5),(5,0),(-5,0),(1,4),(-1,-4),(4,1),(-4,-1),(1,6),(-1,-6),(6,1),(-6,-1),(1,1),(-1,-1),(1,-1),(-1,1),(5,5),(-5,-5),(5,-5),(-5,5),(1,5),(-1,-5),(1,-5),(-1,5),(5,1),(-5,-1),(5,-1),(-5,1)]
    return {f"{(A+da)%10}{(B+db)%10}" for da, db in PAT}

# Lookbacks (Audit based)
DS_DAYS, GL_DAYS, GD_DAYS = [6, 5, 8], [3, 1, 4], [3, 7, 5]

def get_all_pairs(df, t_date):
    hist = df[df['DATE'] < pd.to_datetime(t_date)]
    if hist.empty: return [set()]*7 
    
    p_ds = set().union(*(apply_32(hist.iloc[-lb]['DS']) for lb in DS_DAYS if len(hist)>=lb))
    p_gl = set().union(*(apply_32(hist.iloc[-lb]['GL']) for lb in GL_DAYS if len(hist)>=lb))
    p_gd = set().union(*(apply_32(hist.iloc[-lb]['GD']) for lb in GD_DAYS if len(hist)>=lb))
    
    triple = p_ds & p_gl & p_gd
    ds_gl = (p_ds & p_gl) - triple
    ds_gd = (p_ds & p_gd) - triple
    gl_gd = (p_gl & p_gd) - triple # Gali + Gaziabad common
    
    return triple, ds_gl, ds_gd, gl_gd

uploaded_file = st.file_uploader("Upload 0DSP0 File", type=['xlsx'], label_visibility="collapsed")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    for c in ['DS','FD','GD','GL','DB','SG']: df[c] = df[c].apply(get_val_str)
    
    t_date = st.date_input("Select Date", df['DATE'].max())
    actual_ds = df[df['DATE'] == pd.to_datetime(t_date)]['DS'].values[0] if not df[df['DATE'] == pd.to_datetime(t_date)].empty else ""

    triple, ds_gl, ds_gd, gl_gd = get_all_pairs(df, t_date)

    st.write(f"### 📅 {t_date.strftime('%d-%b')} Logic Dashboard")
    
    # Grid Display
    rows = st.columns(4)
    titles = ["🏆 TRIPLE", "🤝 DS + GL", "🤝 DS + GD", "🔥 GL + GD"]
    data_list = [triple, ds_gl, ds_gd, gl_gd]
    colors = ["gold", "#007bff", "#007bff", "#FF4B4B"] # GL+GD ko Red highlight diya hai

    for i, data in enumerate(data_list):
        with rows[i]:
            st.markdown(f"<div style='background:{colors[i]}; color:white; text-align:center; font-weight:bold; padding:2px;'>{titles[i]}</div>", unsafe_allow_html=True)
            html = "<div class='compact-grid'>"
            for n in sorted(list(data)):
                bg = "#28a745" if n == actual_ds else "#f0f2f6"
                html += f"<div class='item' style='background:{bg};'>{n}</div>"
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

    # --- 11-Day History with Logic Tracking ---
    st.markdown("---")
    st.subheader("📜 11-Day Bar & Date Audit (Pair Tracking)")
    hist_view = df[df['DATE'] <= pd.to_datetime(t_date)].tail(11).copy().sort_values('DATE', ascending=False)
    
    audit_data = []
    for _, row in hist_view.iterrows():
        t, dgl, dgd, glgd = get_all_pairs(df, row['DATE'])
        val = row['DS']
        win = val
        if val in t: win = f"🏆 {val} (Triple)"
        elif val in glgd: win = f"🔥 {val} (GL+GD)"
        elif val in dgl: win = f"🤝 {val} (DS+GL)"
        elif val in dgd: win = f"🤝 {val} (DS+GD)"
        
        audit_data.append({"Tarikh": row['DATE'].strftime('%d-%m'), "Bar": row['DATE'].strftime('%A'), "DS Result": win, "GL": row['GL'], "GD": row['GD']})
    
    st.table(pd.DataFrame(audit_data))
  
