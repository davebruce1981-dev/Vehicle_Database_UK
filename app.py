import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Recovery Specs", layout="centered")

# CENTRALIZED URL FOR THE GOOGLE APPS SCRIPT
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzcjYzl5kmbGMfy90KXxO8b18E-eWYK-Xc9EAOxwROFtDoOQHePYduTXMEfiTarb7Jh/exec"

st.markdown("""
    <style>
    /* Global Reset to ensure full viewport usage */
    html, body { margin: 0; padding: 0; height: 100%; overflow-x: hidden; }

    /* Top Hazard Tape */
    body::before {
        content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 20px; z-index: 999999;
        background: repeating-linear-gradient(45deg, #000000, #000000 20px, #f6782a 20px, #f6782a 40px);
    }
    
    /* Bottom Hazard Tape */
    body::after {
        content: ""; position: fixed; bottom: 0; left: 0; width: 100%; height: 20px; z-index: 999999;
        background: repeating-linear-gradient(45deg, #000000, #000000 20px, #f6782a 20px, #f6782a 40px);
    }

    /* Left Hazard Tape */
    .stApp::before {
        content: ""; position: fixed; top: 0; left: 0; width: 20px; height: 100%; z-index: 999999;
        background: repeating-linear-gradient(45deg, #000000, #000000 20px, #f6782a 20px, #f6782a 40px);
    }

    /* Right Hazard Tape */
    .stApp::after {
        content: ""; position: fixed; top: 0; right: 0; width: 20px; height: 100%; z-index: 999999;
        background: repeating-linear-gradient(45deg, #000000, #000000 20px, #f6782a 20px, #f6782a 40px);
    }

    /* Adjust main container to prevent content overlap on all 4 sides */
    .stApp { 
        background-color: #000000 !important; 
        padding: 40px 40px !important; 
    }
    
    h1, h2, h3, h4, p, label { color: #ffffff !important; }
    
    div[data-testid="stVerticalBlock"] div.stButton > button, 
    div[data-testid="stFormSubmitButton"] button { 
        background-color: #f6782a !important; color: white !important; width: 100%; font-weight: bold; border: none !important;
    }
    
    .result-header { font-size: 1.15em !important; color: #f6782a !important; font-weight: bold; margin-bottom: 2px; }
    .stExpander { border: 1px solid #333333 !important; background-color: #111111 !important; margin-bottom: 10px; }
    
    /* --- MAGIC HAMBURGER CSS --- */
    [data-testid="collapsedControl"] svg { display: none !important; }
    [data-testid="collapsedControl"]::after {
        content: "☰";
        font-size: 26px;
        color: #ffffff;
        font-weight: bold;
        padding-left: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- SELF-HEALING DATA FETCHING ---
@st.cache_data(ttl=5) 
def load_data():
    url_with_sheet = "https://docs.google.com/spreadsheets/d/1T7k-8tjbsZd0mpcfFzKpb3yisaxwLmOpoJeGQXXYc8M/gviz/tq?tqx=out:csv&sheet=Vehicle_Library"
    url_fallback = "https://docs.google.com/spreadsheets/d/1T7k-8tjbsZd0mpcfFzKpb3yisaxwLmOpoJeGQXXYc8M/export?format=csv"
    
    df = pd.DataFrame()
    try:
        df = pd.read_csv(url_with_sheet)
    except:
        pass
        
    if df.empty or not any(x in [str(c).strip().lower() for c in df.columns] for x in ['make', 'brand']):
        try:
            df = pd.read_csv(url_fallback)
        except Exception as e:
            st.error(f"Google Connection Failed entirely: {e}")
            return pd.DataFrame(columns=['Make', 'Model', 'Year Range', 'Clean_Model'])
            
    df.columns = df.columns.str.strip()
    rename_dict = {}
    for col in df.columns:
        cleaned = str(col).strip().lower()
        if cleaned == 'make': rename_dict[col] = 'Make'
        elif cleaned == 'model': rename_dict[col] = 'Model'
        elif cleaned == 'year range': rename_dict[col] = 'Year Range'
    if rename_dict:
        df = df.rename(columns=rename_dict)
        
    return df

@st.cache_data(ttl=600)
def load_sidebar_data():
    url = "https://docs.google.com/spreadsheets/d/1T7k-8tjbsZd0mpcfFzKpb3yisaxwLmOpoJeGQXXYc8M/gviz/tq?tqx=out:csv&sheet=Sidebar"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

def is_valid(val):
    if pd.isna(val): return False
    str_val = str(val).strip().lower()
    return str_val != 'nan' and str_val != ''

# --- SIDEBAR MENU ---
def show_sidebar_menu():
    try:
        side_df = load_sidebar_data()
        with st.sidebar:
            st.header("📚 Generic Resources")
            st.divider()
            
            if side_df.empty or not all(col in side_df.columns for col in ['Category', 'Sub-Category', 'Link']):
                return
            
            categories = side_df['Category'].dropna().unique()
            for cat in categories:
                if is_valid(cat):
                    st.subheader(f"🗂️ {cat}")
                    subset = side_df[side_df['Category'] == cat]
                    for _, row in subset.iterrows():
                        sub_cat = str(row.get('Sub-Category', 'Resource')).strip()
                        link = str(row.get('Link', '')).strip()
                        if not is_valid(link) or link == 'nan': link = "https://example.com"
                        elif not link.startswith("http"): link = "https://" + link
                        if is_valid(sub_cat) and sub_cat != 'nan':
                            st.link_button(f"🔗 {sub_cat}", url=link, use_container_width=True)
                    st.write("") 
    except Exception as e:
        st.sidebar.error(f"Sidebar error: {e}")

# --- MAIN APP ---
def main():
    try:
        st.image("Recoveryspecs logo.jpeg", use_container_width=True)
    except:
        pass

    df = load_data()

    if 'Make' not in df.columns or 'Model' not in df.columns:
        st.error("### 🚨 Connection Error: Cannot locate standard data columns. Check spreadsheet layout.")
        if not df.empty:
            st.warning(f"Columns seen by system: {list(df.columns)}")
        return 

    # Guaranteed creation of Clean_Model column safely
    df['Clean_Model'] = df['Model'].apply(lambda x: re.sub(r'\s*\(.*?\)', '', str(x)).strip() if pd.notna(x) else "")
    
    if 'show_results' not in st.session_state: st.session_state.show_results = False

    if not st.session_state.show_results:
        show_sidebar_menu()
        st.subheader("Search Specs")

        # 1. SAFE MAKE SELECTION
        make_options = [""]
        if 'Make' in df.columns and not df.empty:
            make_options += sorted(df['Make'].dropna().unique().astype(str))
            
        selected_make = st.selectbox("MAKE", options=make_options)
        
        # Filter rows by Make safely
        if 'Make' in df.columns and selected_make and not df.empty:
            filtered_by_make = df[df['Make'] == selected_make]
        else:
            filtered_by_make = df
        
        # 2. THE ULTIMATE KEYERROR SHIELD FOR MODEL
        model_options = [""]
        if not filtered_by_make.empty:
            if 'Clean_Model' in filtered_by_make.columns:
                model_options += sorted(filtered_by_make['Clean_Model'].dropna().unique().astype(str))
            elif 'Model' in filtered_by_make.columns:
                fallback_clean = filtered_by_make['Model'].apply(lambda x: re.sub(r'\s*\(.*?\)', '', str(x)).strip() if pd.notna(x) else "")
                model_options += sorted(fallback_clean.dropna().unique().astype(str))

        selected_model = st.selectbox("MODEL", options=model_options)
        
        # Filter rows by Model safely
        if not filtered_by_make.empty and selected_model:
            if 'Clean_Model' in filtered_by_make.columns:
                filtered_by_model = filtered_by_make[filtered_by_make['Clean_Model'] == selected_model]
            elif 'Model' in filtered_by_make.columns:
                temp_clean = filtered_by_make['Model'].apply(lambda x: re.sub(r'\s*\(.*?\)', '', str(x)).strip() if pd.notna(x) else "")
                filtered_by_model = filtered_by_make[temp_clean == selected_model]
            else:
                filtered_by_model = filtered_by_make
        else:
            filtered_by_model = filtered_by_make
        
        # 3. SAFE YEAR RANGE SELECTION
        year_options = [""]
        if not filtered_by_model.empty and 'Year Range' in filtered_by_model.columns:
            year_options += sorted(filtered_by_model['Year Range'].dropna().unique().astype(str))
            
        selected_year = st.selectbox("YEAR RANGE", options=year_options)

        if st.button("🔍 SEARCH SPECS", use_container_width=True):
            if not filtered_by_model.empty and selected_year and 'Year Range' in filtered_by_model.columns:
                st.session_state.results = filtered_by_model[filtered_by_model['Year Range'] == selected_year]
            else:
                st.session_state.results = filtered_by_model
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
                    except Exception as e: 
                        st.error(f"Error submitting: {e}")
    else:
        st.markdown("<style>[data-testid='collapsedControl'] { display: none !important; }</style>", unsafe_allow_html=True)
        results = st.session_state.results
        
        if len(results) == 1:
            record = results.iloc[0]
            st.subheader(f"{record.get('Make', '')} {record.get('Model', '')} | {record.get('Year Range', '')}")
            st.divider()

            sections = {
                "🔋 BATTERY DETAILS": ["battery"], 
                "🏋️ JACKING POINTS": ["jack", "torque"], 
                "🔌 OBD LOCATION": ["obd", "odb"],
                "🅿️ HANDBRAKE RELEASE": ["electric handbrake", "handbrake release"],
                "⚙️ GEAR NEUTRAL OVERRIDE": ["automatic gear", "neutral override"],
                "🚛 HEAVY RECOVERY": ["propshaft", "half-shaft", "half shaft", "towing", "airline connectors", "cab tilt"]
            }
            
            displayed = {'Make', 'Model', 'Year Range', 'Clean_Model'}
            
            for label, keywords in sections.items():
                with st.expander(label):
                    matched_any_columns = False
                    
                    for col in record.index:
                        if any(k in col.lower() for k in keywords) and col not in displayed:
                            matched_any_columns = True
                            val = str(record[col])
                            
                            st.markdown(f'<p class="result-header">{col}</p>', unsafe_allow_html=True)
                            
                            if is_valid(val):
                                if "http" in val.lower() and ("photo" in col.lower() or val.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))):
                                    img_src = val
                                    if "drive.google.com" in val or "docs.google.com" in val:
                                        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', val) or re.search(r'id=([a-zA-Z0-9_-]+)', val)
                                        if match:
                                            file_id = match.group(1)
                                            img_src = f"https://drive.google.com/thumbnail?id={file_id}&sz=w400"

                                    st.markdown(f"""
                                        <a href="{val}" target="_blank">
                                            <img src="{img_src}" style="width:150px; height:150px; object-fit:cover; border-radius:8px; cursor:pointer; margin-bottom:10px;">
                                        </a>
                                    """, unsafe_allow_html=True)
                                elif "http" in val.lower():
                                    st.link_button(f"🌐 View {col}", url=val)
                                else:
                                    st.write(val)
                            else:
                                st.write("*No data yet*")
                                if "photo" in col.lower():
                                    action = st.radio(f"Action for {col}:", ["Upload Photo", "Take New Photo"], key=f"radio_{col}_{record.name}")
                                    img_file = st.file_uploader(f"Choose file", type=['jpg', 'png', 'jpeg'], key=f"uploader_{col}_{record.name}") if action == "Upload Photo" else st.camera_input(f"Camera", key=f"camera_{col}_{record.name}")
                                    if img_file and st.button(f"Submit Photo for {col}", key=f"btn_{col}_{record.name}"):
                                        bytes_data = img_file.getvalue()
                                        base64_str = base64.b64encode(bytes_data).decode('utf-8')
                                        try:
                                            requests.post(GOOGLE_SCRIPT_URL, json={
                                                "type": "photo", 
                                                "make": record['Make'], 
                                                "model": record['Model'], 
                                                "year": record.get('Year Range', ''),
                                                "column": col, 
                                                "image": base64_str
                                            })
                                            st.success("Uploaded successfully!")
                                        except Exception as e:
                                            st.error(f"Upload failed: {e}")
                                else:
                                    with st.form(f"form_{col}_{record.name}"):
                                        new_val = st.text_input("Add info")
                                        if st.form_submit_button("Submit"):
                                            try:
                                                requests.post(GOOGLE_SCRIPT_URL, json={
                                                    "type": "update", 
                                                    "make": record['Make'], 
                                                    "model": record['Model'], 
                                                    "year": record.get('Year Range', ''),
                                                    "column": col, 
                                                    "newValue": new_val
                                                })
                                                st.success("Submitted successfully!")
                                            except Exception as e:
                                                st.error(f"Submission failed: {e}")
                            displayed.add(col)
                    
                    if not matched_any_columns:
                        st.write("*No active specification columns found for this category.*")
            
            with st.expander("🧩 OTHER SPECIFICATIONS"):
                found_other = False
                for col in record.index:
                    if col not in displayed and is_valid(record[col]):
                        val = str(record[col])
                        if "http" in val.lower() or "link" in col.lower() or "yuasa" in col.lower() or "dvla" in col.lower():
                            st.link_button(f"🌐 {col}", url=val, use_container_width=True)
                        else:
                            st.write(f"**{col}:** {val}")
                        found_other = True
                if not found_other: 
                    st.write("No additional unique information recorded.")
            
            st.write("")
            with st.expander("📝 Suggest a Spec Update or Correction"):
                with st.form(f"universal_update_{record.name}"):
                    up_col = st.selectbox("Which field needs updating?", options=[c for c in df.columns if c not in ['Make', 'Model', 'Year Range', 'Clean_Model']])
                    new_val = st.text_input("Correct information / notes:")
                    if st.form_submit_button("Submit Entry"):
                        try:
                            requests.post(GOOGLE_SCRIPT_URL, json={
                                "type": "update", 
                                "make": record['Make'], 
                                "model": record['Model'], 
                                "year": record.get('Year Range', ''),
                                "column": up_col, 
                                "newValue": new_val
                            })
                            st.success("Correction logged for review!")
                        except Exception as e:
                            st.error(f"Submission failed: {e}")

            if st.button("⬅️ Back to Search"):
                st.session_state.show_results = False
                st.rerun()
        else:
            for idx, row in results.iterrows():
                r_make = row.get('Make', 'Unknown Make')
                r_model = row.get('Model', 'Unknown Model')
                r_year = row.get('Year Range', 'N/A')
                if st.button(f"{r_make} | {r_model} | {r_year}", key=f"list_{idx}", use_container_width=True):
                    st.session_state.results = results.loc[[idx]]
                    st.rerun()

if __name__ == "__main__":
    main()
