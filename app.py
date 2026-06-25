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
    [data-testid="collapsedControl"]::after { content: "☰"; font-size: 26px; color: #ffffff; font-weight: bold; padding-left: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- UTILS ---
@st.cache_data(ttl=600)
def load_sheet(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/1T7k-8tjbsZd0mpcfFzKpb3yisaxwLmOpoJeGQXXYc8M/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

def is_valid(val):
    s = str(val).strip().lower()
    return pd.notna(val) and s != 'nan' and s != ''

# --- MAIN APP ---
def main():
    try: st.image("Recoveryspecs logo.jpeg", use_container_width=True)
    except: pass

    df = load_sheet("Vehicle_Library")
    df['Clean_Model'] = df['Model'].apply(lambda x: re.sub(r'\s*\(.*?\)', '', str(x)).strip())
    
    if 'show_results' not in st.session_state: st.session_state.show_results = False

    if not st.session_state.show_results:
        # Sidebar
        with st.sidebar:
            st.header("📚 Generic Resources")
            side_df = load_sheet("Sidebar")
            for _, row in side_df.iterrows():
                if is_valid(row['Category']):
                    st.link_button(f"🔗 {row['Sub-Category']}", url=str(row['Link']), use_container_width=True)

        st.subheader("Search Specs")
        make = st.selectbox("MAKE", [""] + sorted(df['Make'].dropna().unique()))
        f_df = df if not make else df[df['Make'] == make]
        
        model = st.selectbox("MODEL", [""] + sorted(f_df['Clean_Model'].unique()))
        f_df = f_df if not model else f_df[f_df['Clean_Model'] == model]
        
        year = st.selectbox("YEAR RANGE", [""] + sorted(f_df['Year Range'].unique()))

        if st.button("🔍 SEARCH SPECS", use_container_width=True):
            st.session_state.results = f_df[f_df['Year Range'] == year] if year else f_df
            st.session_state.show_results = True
            st.rerun()

        with st.expander("➕ Report Missing Vehicle"):
            with st.form("add_v"):
                n_data = {k: st.text_input(k) for k in ["Make", "Model", "Year Range", "Details"]}
                if st.form_submit_button("Submit"):
                    requests.post(GOOGLE_SCRIPT_URL, json={"type": "new_request", **n_data})
                    st.success("Submitted!")
    else:
        st.markdown('<style>[data-testid="collapsedControl"] { display: none !important; }</style>', unsafe_allow_html=True)
        res = st.session_state.results
        
        if len(res) == 1:
            r = res.iloc[0]
            st.subheader(f"{r['Make']} {r['Model']} | {r['Year Range']}")
            # Display logic remains your existing expander structure...
            if st.button("⬅ Back"):
                st.session_state.show_results = False
                st.rerun()
        else:
            for idx, row in res.iterrows():
                if st.button(f"{row['Make']} {row['Model']} ({row['Year Range']})", key=idx):
                    st.session_state.results = res.loc[[idx]]
                    st.rerun()

if __name__ == "__main__":
    main()