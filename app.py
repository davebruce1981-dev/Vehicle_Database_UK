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
    </style>
""", unsafe_allow_html=True)

# --- DATA FETCHING ---
@st.cache_data(ttl=600)
def load_data():
    # Using your specific Sheet ID and the Viz API
    url = "https://docs.google.com/spreadsheets/d/1T7k-8tjbsZd0mpcfFzKpb3yisaxwLmOpoJeGQXXYc8M/gviz/tq?tqx=out:csv&sheet=Vehicle_Library"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Diagnostic print to see what data is actually arriving
        print("Data columns found:", df.columns.tolist())
        print("First row sample:", df.head(1).to_dict())
        
        # Ensure we have the basic columns, even if empty
        for col in ['Make', 'Model', 'Year Range']:
            if col not in df.columns:
                df[col] = "N/A"
        
        return df
    except Exception as e:
        st.error(f"Error connecting to Google Sheet: {e}")
        return pd.DataFrame(columns=['Make', 'Model', 'Year Range'])

# --- MAIN APP ---
def main():
    df = load_data()
    
    if df.empty:
        st.warning("The spreadsheet is empty or could not be reached. Please check: 1. Share settings set to 'Anyone with link' 2. Correct tab name.")
        return

    # Clean models
    df['Clean_Model'] = df['Model'].apply(lambda x: re.sub(r'\s*\(.*?\)', '', str(x)).strip())
    
    st.subheader("Search Specs")

    # Dropdowns
    makes = [""] + sorted([m for m in df['Make'].unique() if pd.notna(m)])
    selected_make = st.selectbox("MAKE", options=makes)
    
    filtered_by_make = df if not selected_make else df[df['Make'] == selected_make]
    
    models = [""] + sorted([m for m in filtered_by_make['Clean_Model'].unique() if pd.notna(m)])
    selected_model = st.selectbox("MODEL", options=models)
    
    filtered_by_model = filtered_by_make if not selected_model else filtered_by_make[filtered_by_make['Clean_Model'] == selected_model]
    
    years = [""] + sorted([y for y in filtered_by_model['Year Range'].unique() if pd.notna(y)])
    selected_year = st.selectbox("YEAR RANGE", options=years)

    if st.button("🔍 SEARCH"):
        if not selected_make or not selected_model:
            st.error("Please select a Make and Model.")
        else:
            st.success(f"Found match for {selected_make} {selected_model}")
            # Display results logic here...

if __name__ == "__main__":
    main()
