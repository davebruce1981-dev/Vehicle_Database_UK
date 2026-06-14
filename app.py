import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Recovery Specs", layout="centered")

# CENTRALIZED URL (Change this once, and it updates everywhere)
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
    # Ensure you have your logo file in the same folder as app.py
    try:
        st.image("Recoveryspecs logo.jpeg", use_container_width=True)
    except:
        pass

    df = load_data()
    if 'Model' in df.columns:
        df['Clean_Model'] = df['Model'].apply(lambda x: re.sub(r'\s*\(.*?\)', '', str(x)).strip())
    
    if 'show_results' not in st.session_state: st.session_state.show_results = False

    if not st.session_state.show_results:
        st.subheader("Search Specs")

        selected_make = st.selectbox("MAKE", options=[""] + sorted(df['Make'].dropna().unique().astype(str)))
        filtered_by_make = df if not selected_make else df[df['Make'] == selected_make]
        
        selected_model = st.selectbox("MODEL", options=[""] + sorted(filtered_by_make['Clean_Model'].unique().astype(str)))
        
        if not selected_model:
            filtered_by_model = filtered_by_make
        else:
            filtered_by_model = filtered_by_make[filtered_by_make['Clean_Model'] == selected_model]
        
        selected_year = st.selectbox("YEAR RANGE", options=[""] + sorted(filtered_by_model['Year Range'].unique().astype(str)))

        if st.button("🔍 SEARCH SPECS", use_container_width=True):
            st.session_state.results = filtered_by_model[filtered_by_model['Year Range'] == selected_year] if selected_year else filtered_by_model
            st.session_state.show_results = True
            st.rerun()
            
        st.divider()

        with st.expander("➕ Report Missing Vehicle"):
            with st.form("missing_vehicle_form", clear_on_submit=True):
                n_make = st.text_input("Make")
                n_model = st.text_input("Model")
                n_year = st.text_input("Year Range")
                n_details = st.text_input("Additional Details")
                
                if st.form_submit_button("Submit Request"):
                    payload = {"type": "new_request", "make": n_make, "model": n_model, "year": n_year, "details": n_details}
                    try:
                        requests.post(GOOGLE_SCRIPT_URL, json=payload)
                        st.success("Request submitted successfully!")
                    except: st.error("Error submitting.")

    else:
        results = st.session_state.results
        if len(results) == 1:
            record = results.iloc[0]
            st.subheader(f"{record.get('Make', '')} {record.get('Model', '')} | {record.get('Year Range', '')}")
            st.divider()

            st.subheader("General Details")
            for col in ['Fuel Type', 'Drivetrain', 'Engine']:
                if col in record.index and is_valid(record[col]):
                    st.write(f"**{col}:** {record[col]}")
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
                                # Check if it is a photo column or image link
                                if "http" in val.lower() and ("photo" in col.lower() or val.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))):
                                    
                                    # --- GOOGLE DRIVE DIRECT LINK CONVERTER (THUMBNAIL API) ---
                                    img_src = val
                                    if "drive.google.com/file/d/" in val:
                                        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', val)
                                        if match:
                                            file_id = match.group(1)
                                            # Use Google's thumbnail API for reliable embedding
                                            img_src = f"https://drive.google.com/thumbnail?id={file_id}&sz=w400"
                                    # ------------------------------------------

                                    st.markdown(f"""
                                        <a href="{val}" target="_blank">
                                            <img src="{img_src}" style="width:150px; height:150px; object-fit:cover; border-radius:8px; cursor:pointer; margin-bottom:10px;">
                                        </a>
                                    """, unsafe_allow_html=True)
                                elif "http" in val.lower():
                                    # If it's a link but not an image, show a button
                                    st.link_button(f"🌐 View {col}", url=val)
                                else:
                                    # Standard text
                                    st.write(val)
                            else:
                                st.write("*No data yet*")
                                if "photo" in col.lower():
                                    action = st.radio(f"Action for {col}:", ["Upload Photo", "Take New Photo"], key=f"radio_{col}")
                                    img_file = st.file_uploader(f"Choose file", type=['jpg', 'png', 'jpeg'], key=f"uploader_{col}") if action == "Upload Photo" else st.camera_input(f"Camera", key=f"camera_{col}")
                                    if img_file and st.button(f"Submit Photo for {col}", key=f"btn_{col}"):
                                        bytes_data = img_file.getvalue()
                                        base64_str = base64.b64encode(bytes_data).decode('utf-8')
                                        requests.post(GOOGLE_SCRIPT_URL, json={"type": "photo", "make": record['Make'], "model": record['Model'], "column": col, "image": base64_str})
                                        st.success("Uploaded!")
                                else:
                                    with st.form(f"form_{col}_{record.name}"):
                                        new_val = st.text_input(f"Add info")
                                        if st.form_submit_button("Submit"):
                                            requests.post(GOOGLE_SCRIPT_URL, json={"type": "update", "make": record['Make'], "model": record['Model'], "column": col, "newValue": new_val})
                                            st.success("Submitted!")
                            displayed.add(col)
            
            with st.expander("⚙️ OTHER SPECIFICATIONS"):
                found_other = False
                for col in record.index:
                    if col not in displayed and is_valid(record[col]):
                        val = str(record[col])
                        # Standard link buttons for Other Specs
                        if "http" in val.lower() or "link" in col.lower() or "yuasa" in col.lower() or "dvla" in col.lower():
                            st.link_button(f"🌐 {col}", url=val, use_container_width=True)
                        else:
                            st.write(f"**{col}:** {val}")
                        found_other = True
                
                if not found_other:
                    st.write("No additional information available.")
            
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
