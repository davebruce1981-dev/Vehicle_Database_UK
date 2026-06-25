import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Recovery Specs", layout="centered")
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzcjYzl5kmbGMfy90KXxO8b18E-eWYK-Xc9EAOxwROFtDoOQHePYduTXMEfiTarb7Jh/exec"

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    h1, h2, h3, h4, p, label { color: #ffffff !important; }
    div[data-testid="stVerticalBlock"] div.stButton > button, 
    div[data-testid="stFormSubmitButton"] button { 
        background-color: #f6782a !important; color: white !important; width: 100%; font-weight: bold; border: none !important;
    }
    .result-header { font-size: 1.15em !important; color: #f6782a !important; font-weight: bold; margin-bottom: 2px; }
    .stExpander { border: 1px solid #333333 !important; background-color: #111111 !important; margin-bottom: 10px; }
    [data-testid="collapsedControl"] svg { display: none !important; }
    [data-testid="collapsedControl"]::after {
        content: "☰"; font-size: 26px; color: #ffffff; font-weight: bold; padding-left: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA FETCHING ---
@st.cache_data(ttl=600)
def load_all_data():
    # Define your sheets here
    sheets = ["Vehicle_Library", "Motorcycles", "Vans", "HGV"]
    sheet_labels = {
        "Vehicle_Library": "Car / Light Commercial",
        "Motorcycles": "Motorcycle",
        "Vans": "Van",
        "HGV": "HGV"
    }
    
    df_list = []
    base_url = "https://docs.google.com/spreadsheets/d/1T7k-8tjbsZd0mpcfFzKpb3yisaxwLmOpoJeGQXXYc8M/gviz/tq?tqx=out:csv&sheet="
    
    for sheet in sheets:
        try:
            df = pd.read_csv(f"{base_url}{sheet}")
            df.columns = df.columns.str.strip()
            df['Vehicle Category'] = sheet_labels.get(sheet, sheet)
            df_list.append(df)
        except Exception as e:
            st.error(f"Error loading '{sheet}': {e}")
            
    return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

def is_valid(val):
    if pd.isna(val): return False
    str_val = str(val).strip().lower()
    return str_val != 'nan' and str_val != ''

# --- MAIN ---
def main():
    try: st.image("Recoveryspecs logo.jpeg", use_container_width=True)
    except: pass

    df = load_all_data()
    if df.empty:
        st.error("No data found.")
        return

    # Clean models for dropdown
    if 'Model' in df.columns:
        df['Clean_Model'] = df['Model'].apply(lambda x: re.sub(r'\s*\(.*?\)', '', str(x)).strip())

    if 'show_results' not in st.session_state: st.session_state.show_results = False

    if not st.session_state.show_results:
        st.subheader("Search Specs")
        make = st.selectbox("MAKE", options=[""] + sorted(df['Make'].dropna().unique().astype(str)))
        filtered = df if not make else df[df['Make'] == make]
        
        model = st.selectbox("MODEL", options=[""] + sorted(filtered['Clean_Model'].unique().astype(str)))
        filtered = filtered if not model else filtered[filtered['Clean_Model'] == model]
        
        year = st.selectbox("YEAR RANGE", options=[""] + sorted(filtered['Year Range'].unique().astype(str)))

        if st.button("🔍 SEARCH SPECS", use_container_width=True):
            st.session_state.results = filtered[filtered['Year Range'] == year] if year else filtered
            st.session_state.show_results = True
            st.rerun()
    else:
        results = st.session_state.results
        if len(results) == 1:
            record = results.iloc[0]
            st.subheader(f"{record.get('Make', '')} {record.get('Model', '')}")
            st.write(f"**Category:** {record.get('Vehicle Category', 'N/A')}")
            
            if st.button("⬅ Back to Search"):
                st.session_state.show_results = False
                st.rerun()
        else:
            for idx, row in results.iterrows():
                if st.button(f"{row['Vehicle Category']} | {row['Make']} {row['Model']}", key=idx):
                    st.session_state.results = results.loc[[idx]]
                    st.rerun()

if __name__ == "__main__":
    main()