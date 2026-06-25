import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- CONFIG ---
st.set_page_config(page_title="Recovery Specs", layout="centered")
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzcjYzl5kmbGMfy90KXxO8b18E-eWYK-Xc9EAOxwROFtDoOQHePYduTXMEfiTarb7Jh/exec"

# --- DATA FETCHING ---
@st.cache_data(ttl=1)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1T7k-8tjbsZd0mpcfFzKpb3yisaxwLmOpoJeGQXXYc8M/gviz/tq?tqx=out:csv&sheet=Vehicle_Library"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

# --- MAIN APP ---
def main():
    st.title("Recovery Specs")
    df = load_data()
    
    # DEBUG: See what is happening
    if df.empty:
        st.error("Data not found. Please ensure the 'Vehicle_Library' tab exists.")
        return
    
    # Logic for Selectboxes
    if 'Make' in df.columns:
        makes = [""] + sorted([m for m in df['Make'].dropna().unique()])
        selected_make = st.selectbox("MAKE", options=makes)
        
        filtered_df = df[df['Make'] == selected_make] if selected_make else df
        
        if 'Model' in filtered_df.columns:
            models = [""] + sorted([m for m in filtered_df['Model'].dropna().unique()])
            selected_model = st.selectbox("MODEL", options=models)
            
            if selected_model:
                st.success(f"Selected: {selected_make} {selected_model}")
                # You can add display logic here
    else:
        st.error(f"Columns not found! Found: {df.columns.tolist()}")

if __name__ == "__main__":
    main()
