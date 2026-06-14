import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Recovery Specs", layout="centered")

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
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1T7k-8tjbsZd0mpcfFzKpb3yisaxwLmOpoJeGQXXYc8M/gviz/tq?tqx=out:csv&sheet=Vehicle_Library"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

def is_valid(val):
    if pd.isna(val): return False
    str_val = str(val).strip().lower()
    return str_val != 'nan' and str_val != ''

def main():
    col1, col2, col3 = st.columns([1, 4, 1]) 
    with col2: st.image("Recoveryspecs logo.jpeg", use_container_width=True)

    df = load_data()
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
            st.subheader(f"{record.get('Make', '')} {record.get('Model', '')}")
            st.divider()

            sections = {
                "🪫 BATTERY DETAILS": ["battery"],
                "🏋️ JACKING POINTS": ["jack", "torque"],
                "🔌 OBD LOCATION": ["obd", "odb"]
            }

            displayed = {'Make', 'Model', 'Year Range', 'Fuel Type', 'Drivetrain', 'Clean_Model'}
            
            for label, keywords in sections.items():
                with st.expander(label):
                    found_any = False
                    for col in record.index:
                        if any(k in col.lower() for k in keywords) and col not in displayed:
                            val = str(record[col])
                            has_data = is_valid(val)
                            
                            st.markdown(f'<p class="result-header">{col}</p>', unsafe_allow_html=True)
                            
                            if has_data:
                                st.write(val)
                            else:
                                st.write("*No data yet*")
                                
                                # --- PHOTO LOGIC ---
                                if "photo" in col.lower():
                                    img_file = st.camera_input(f"Take photo for {col}")
                                    if img_file is not None:
                                        if st.button("Upload Photo"):
                                            # Convert image to base64 for transmission
                                            bytes_data = img_file.getvalue()
                                            base64_str = base64.b64encode(bytes_data).decode('utf-8')
                                            
                                            payload = {
                                                "type": "photo", 
                                                "make": record['Make'], 
                                                "model": record['Model'], 
                                                "column": col, 
                                                "image": base64_str
                                            }
                                            try:
                                                requests.post("https://script.google.com/macros/s/AKfycbw1BzmjWIhqvgwEKbPzJdSz6JgpkDi11KnAM-IGcP8o495lnGWKFK6THoEigf8nXpjc/exec", json=payload)
                                                st.success("Photo uploaded successfully!")
                                            except: st.error("Error uploading photo.")
                                else:
                                    # Standard text input form
                                    with st.form(f"form_{col}_{record.name}"):
                                        new_val = st.text_input(f"Add info for {col}")
                                        if st.form_submit_button("Submit for Approval"):
                                            payload = {"type": "update", "make": record['Make'], "model": record['Model'], "column": col, "newValue": new_val}
                                            try:
                                                requests.post("https://script.google.com/macros/s/AKfycbw1BzmjWIhqvgwEKbPzJdSz6JgpkDi11KnAM-IGcP8o495lnGWKFK6THoEigf8nXpjc/exec", json=payload)
                                                st.success("Submitted!")
                                            except: st.error("Error submitting.")
                            
                            displayed.add(col)
                            found_any = True
                    if not found_any: st.info("No specific data found for this category.")
            
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
