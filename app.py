import pandas as pd
import streamlit as st
from collections import Counter, defaultdict  # <-- Yahan Counter add kar diya hai

st.set_page_config(layout="wide", page_title="MAYA AI: GOLDEN QUADRUPLE FIX")

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

# --- 8 Golden Ank Logic ---
def get_golden_8(df, t_date):
    hist = df[df['DATE'] < pd.to_datetime(t_date)].tail(30)
    all_vals = []
    # DS, GL, GD teeno se repeat hone wale top 8 uthayenge
    for c in ['DS','GL','GD']: 
        all_vals.extend(
            
