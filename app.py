import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Recovery Specs", layout="centered")

# CENTRALIZED URL
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

# --- DATA FETCHING ---
@st.cache_data(ttl=10) # 10 seconds cache for live building & testing updates
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1T7k-8tjbsZd0mpcfFzKpb3yisaxwLmOpoJeGQXXYc8M/gviz/tq?tqx=out:csv&sheet=Vehicle_Library"
    try:
        df = pd.read_csv(url)
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
    except Exception as e:
        return pd.DataFrame(columns=['Make', 'Model', 'Year Range'])

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

    if 'Make' not in df.columns:
        st.error("### 🚨 Connection Error: Cannot find the Vehicle Data sheet tab.")
        return 

    if 'Model' in df.columns:
        df['Clean_Model'] = df['Model'].apply(lambda x: re.sub(r'\s*\(.*?\)', '', str(x)).strip())
    
    if 'show_results' not in st.session_state: st.session_state.show_results = False

    if not st.session_state.show_results:
        show_sidebar_menu()
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

            st.subheader("General Details")
            for col in ['Fuel Type', 'Drivetrain', 'Engine']:
                if col in record.index and is_valid(record[col]):
                    st.write(f"**{col}:** {record[col]}")
            st.divider()

            # Fixed Emoji layout structure
            sections = {
                "🔋 BATTERY DETAILS": ["battery"], 
                "🏋️ JACKING POINTS": ["jack", "torque"], 
                "🔌 OBD LOCATION": ["obd", "odb"],
                "🅿️ HANDBRAKE RELEASE": ["electric handbrake", "handbrake release"],
                "⚙️ GEAR NEUTRAL OVERRIDE": ["automatic gear", "neutral override"],
                "🚛 DRIVETRAIN & TOWING SPECS": ["propshaft", "half-shaft", "half shaft", "towing", "air brake", "cab tilt"]
            }
            
            displayed = {'Make', 'Model', 'Year Range', 'Fuel Type', 'Drivetrain', 'Engine', 'Clean_Model', 'Heavy Vehicle?'}
            
            # Loop through the core expandable menus
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
                                            requests.post(GOOGLE_SCRIPT_URL, json={"type": "photo", "make": record['Make'], "model": record['Model'], "column": col, "image": base64_str})
                                            st.success("Uploaded successfully!")
                                        except Exception as e:
                                            st.error(f"Upload failed: {e}")
                                else:
                                    with st.form(f"form_{col}_{record.name}"):
                                        new_val = st.text_input(f"Add info")
                                        if st.form_submit_button("Submit"):
                                            try:
                                                requests.post(GOOGLE_SCRIPT_URL, json={"type": "update", "make": record['Make'], "model": record['Model'], "column": col, "newValue": new_val})
                                                st.success("Submitted successfully!")
                                            except Exception as e:
                                                st.error(f"Submission failed: {e}")
                            displayed.add(col)
                    
                    if not matched_any_columns:
                        st.write("*No active specification columns found for this category in the Google Sheet.*")
            
            # Positioned perfectly below the core list expanders
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
                    up_col = st.selectbox("Which specification field needs updating?", options=[c for c in df.columns if c not in ['Make', 'Model', 'Year Range', 'Clean_Model', 'Heavy Vehicle?']])
                    new_val = st.text_input("Correct information / notes:")
                    if st.form_submit_button("Submit Entry"):
                        try:
                            requests.post(GOOGLE_SCRIPT_URL, json={"type": "update", "make": record['Make'], "model": record['Model'], "column": up_col, "newValue": new_val})
                            st.success("Correction logged for administrative review!")
                        except Exception as e:
                            st.error(f"Submission communication dropped: {e}")

            if st.button("⬅️ Back to Search"):
                st.session_state.show_results = False
                st.rerun()
        else:
            for idx, row in results.iterrows():
                if st.button(f"{row['Make']} | {row['Model']} | {row['Year Range']}", key=f"list_{idx}", use_container_width=True):
                    st.session_state.results = results.loc[[idx]]
                    st.rerun()

if __name__ == "__main__":
    main()
