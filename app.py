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
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}
    div[data-testid="stVerticalBlock"] div.stButton > button, 
    div[data-testid="stFormSubmitButton"] button { 
        background-color: #f6782a !important; color: white !important; width: 100%; font-weight: bold; border: none !important;
    }
    .result-header { font-size: 1.15em !important; color: #f6782a !important; font-weight: bold; margin-bottom: 2px; }
    .stExpander { border: 1px solid #333333 !important; background-color: #111111 !important; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=600)
def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/1T7k-8tjbsZd0mpcfFzKpb3yisaxwLmOpoJeGQXXYc8M/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip() 
    return df

def is_valid(val):
    if pd.isna(val): return False
    str_val = str(val).strip().lower()
    return str_val != 'nan' and str_val != ''

# --- SIDEBAR MENU ---
def show_sidebar_menu():
    try:
        side_df = load_data("Sidebar")
        with st.sidebar:
            st.header("📚 Generic Resources")
            st.divider()
            categories = side_df['Category'].unique()
            for cat in categories:
                st.subheader(f"🗂️ {cat}")
                subset = side_df[side_df['Category'] == cat]
                for _, row in subset.iterrows():
                    st.link_button(f"🔗 {row['Sub-Category']}", url=row['Link'], use_container_width=True)
                st.write("")
    except:
        st.sidebar.warning("Sidebar data could not be loaded.")

# --- MAIN APP ---
def main():
    show_sidebar_menu()
    
    try:
        st.image("Recoveryspecs logo.jpeg", use_container_width=True)
    except:
        pass

    df = load_data("Vehicle_Library")
    if 'Model' in df.columns:
        df['Clean_Model'] = df['Model'].apply(lambda x: re.sub(r'\s*\(.*?\)', '', str(x)).strip())
    
    if 'show_results' not in st.session_state: st.session_state.show_results = False

    if not st.session_state.show_results:
        st.subheader("Search Specs")
        selected_make = st.selectbox("MAKE", options=[""] + sorted(df['Make'].dropna().unique().astype(str)))
        filtered_by_make = df if not selected_make else df[df['Make'] == selected_make]
        selected_model = st.selectbox("MODEL", options=[""] + sorted(filtered_by_make['Clean_Model'].unique().astype(str)))
        filtered_by_model = filtered_by_make if not selected_model else filtered_by_make[filtered_by_make['Clean_Model'] == selected_model]
        selected_year = st.selectbox("YEAR RANGE", options=[""] + sorted(filtered_by_model['Year Range'].unique().astype(str)))

        if st.button("🔍 SEARCH SPECS", use_container_width=True):
            st.session_state.results = filtered_by_model[filtered_by_model['Year Range'] == selected_year] if selected_year else filtered_by_model
            st.session_state.show_results = True
            st.rerun()
    else:
        results = st.session_state.results
        if len(results) == 1:
            record = results.iloc[0]
            st.subheader(f"{record.get('Make', '')} {record.get('Model', '')} | {record.get('Year Range', '')}")
            st.divider()
            
            sections = {"🪫 BATTERY DETAILS": ["battery"], "🏋️ JACKING POINTS": ["jack", "torque"], "🔌 OBD LOCATION": ["obd", "odb"]}
            displayed = {'Make', 'Model', 'Year Range', 'Fuel Type', 'Drivetrain', 'Engine', 'Clean_Model'}
            
            for label, keywords in sections.items():
                with st.expander(label):
                    for col in record.index:
                        if any(k in col.lower() for k in keywords) and col not in displayed:
                            val = str(record[col])
                            st.markdown(f'<p class="result-header">{col}</p>', unsafe_allow_html=True)
                            if is_valid(val):
                                if "http" in val.lower() and ("photo" in col.lower() or val.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))):
                                    img_src = f"https://drive.google.com/thumbnail?id={re.search(r'/file/d/([a-zA-Z0-9_-]+)', val).group(1)}&sz=w400" if "drive.google.com/file/d/" in val else val
                                    st.markdown(f'<a href="{val}" target="_blank"><img src="{img_src}" style="width:150px; height:150px; object-fit:cover; border-radius:8px; cursor:pointer; margin-bottom:10px;"></a>', unsafe_allow_html=True)
                                elif "http" in val.lower():
                                    st.link_button(f"🌐 View {col}", url=val)
                                else:
                                    st.write(val)
                            displayed.add(col)
            
            with st.expander("⚙️ OTHER SPECIFICATIONS"):
                for col in record.index:
                    if col not in displayed and is_valid(record[col]):
                        val = str(record[col])
                        if "http" in val.lower(): st.link_button(f"🌐 {col}", url=val, use_container_width=True)
                        else: st.write(f"**{col}:** {val}")
            
            if st.button("⬅ Back to Search"):
                st.session_state.show_results = False
                st.rerun()
        else:
            for idx, row in results.iterrows():
                if st.button(f"{row['Make']} | {row['Model']} | {row['Year Range']}", key=f"list_{idx}", use_container_width=True):
                    st.session_state.results = results.loc[[idx]]
                    st.rerun()

if __name__ == "__main__":
    main()
