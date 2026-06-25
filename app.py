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
    
    /* Horizontal radio buttons layout styling */
    div[data-testid="stMarkdownContainer"] p { color: #ffffff !important; }
    
    /* --- MAGIC HAMBURGER CSS --- */
    [data-testid="collapsedControl"] svg {
        display: none !important;
    }
    [data-testid="collapsedControl"]::after {
        content: "☰";
        font-size: 26px;
        color: #ffffff;
        font-weight: bold;
        padding-left: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA FETCHING FUNCTIONS ---
@st.cache_data(ttl=600)
def load_all_data():
    sheets = ["Vehicle_Library", "Motorcycles", "Vans", "HGV"]
    # EXACT match definitions to sync UI and Data perfectly
    sheet_labels = {
        "Vehicle_Library": "Cars / Light Commercial",
        "Motorcycles": "Motorcycles",
        "Vans": "Vans",
        "HGV": "HGV"
    }
    
    df_list = []
    sheet_columns = {} 
    
    for sheet in sheets:
        try:
            url = f"https://docs.google.com/spreadsheets/d/1T7k-8tjbsZd0mpcfFzKpb3yisaxwLmOpoJeGQXXYc8M/gviz/tq?tqx=out:csv&sheet={sheet}"
            df = pd.read_csv(url)
            df.columns = df.columns.str.strip()
            
            # Defensive validation against broken data responses
            if df.empty or len(df.columns) < 2:
                continue
                
            # --- DEFENSIVE COLUMN ALIGNMENT ---
            rename_dict = {}
            for col in df.columns:
                c_low = str(col).strip().lower()
                if 'make' in c_low or 'manufacturer' in c_low:
                    rename_dict[col] = 'Make'
                elif 'model' in c_low:
                    rename_dict[col] = 'Model'
                elif 'year' in c_low:
                    rename_dict[col] = 'Year Range'
                else:
                    rename_dict[col] = str(col).strip()
            df = df.rename(columns=rename_dict)
            
            label = sheet_labels.get(sheet, sheet)
            df['Vehicle Type'] = label
            
            sheet_columns[label] = list(df.columns)
            df_list.append(df)
            
        except Exception as e:
            st.error(f"Error processing tab '{sheet}': {e}")
            
    if df_list:
        combined_df = pd.concat(df_list, ignore_index=True, sort=False)
        for core_col in ['Make', 'Model', 'Year Range']:
            if core_col not in combined_df.columns:
                combined_df[core_col] = ""
        return combined_df, sheet_columns
    else:
        st.error("🚨 Error: No valid data could be compiled from your Google Sheet.")
        return pd.DataFrame(), {}

@st.cache_data(ttl=600)
def load_sidebar_data():
    url = "https://docs.google.com/spreadsheets/d/1T7k-8tjbsZd0mpcfFzKpb3yisaxwLmOpoJeGQXXYc8M/gviz/tq?tqx=out:csv&sheet=Sidebar"
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
        side_df = load_sidebar_data()
        with st.sidebar:
            st.header("📚 Generic Resources")
            st.divider()

            if side_df.empty:
                return

            categories = side_df['Category'].dropna().unique()
            for cat in categories:
                if is_valid(cat):
                    st.subheader(f"🗂️ {cat}")
                    subset = side_df[side_df['Category'] == cat]
                    for _, row in subset.iterrows():
                        sub_cat = str(row.get('Sub-Category', 'Resource')).strip()
                        link = str(row.get('Link', '')).strip()

                        if not is_valid(link) or link == 'nan':
                            link = "https://example.com"
                        elif not link.startswith("http"):
                            link = "https://" + link

                        if is_valid(sub_cat) and sub_cat != 'nan':
                            st.link_button(f"🔗 {sub_cat}", url=link, use_container_width=True)
                    st.write("") 
    except Exception as e:
        st.sidebar.error(f"Sidebar error: {e}")

# --- MAIN APP ---
def main():
    col1, col2, col3 = st.columns([1, 4, 1]) 
    try:
        st.image("Recoveryspecs logo.jpeg", use_container_width=True)
    except:
        pass

    df, sheet_columns = load_all_data()

    if 'show_results' not in st.session_state: st.session_state.show_results = False

    if not st.session_state.show_results:
        show_sidebar_menu()
        st.subheader("Search Specs")

        # --- 1. CATEGORY SELECTION MATCHING YOUR SCREENSHOT ---
        category_options = ["Cars / Light Commercial", "Motorcycles", "Vans", "HGV"]
        selected_category = st.radio("SELECT VEHICLE CATEGORY", options=category_options, horizontal=True)
        
        # Filter data down to the selected category first
        filtered_by_cat = df[df['Vehicle Type'] == selected_category]

        # --- 2. DYNAMIC DROPDOWNS BASED ON SELECTION ---
        if 'Make' in filtered_by_cat.columns:
            make_options = sorted([str(m).strip() for m in filtered_by_cat['Make'].dropna().unique() if str(m).strip().lower() != 'nan' and str(m).strip() != ""])
        else:
            make_options = []

        selected_make = st.selectbox("MAKE", options=[""] + make_options)
        filtered_by_make = filtered_by_cat if not selected_make else filtered_by_cat[filtered_by_cat['Make'] == selected_make]

        if 'Model' in filtered_by_make.columns:
            filtered_by_make['Clean_Model'] = filtered_by_make['Model'].apply(lambda x: re.sub(r'\s*\(.*?\)', '', str(x)).strip())
            model_options = sorted([str(m).strip() for m in filtered_by_make['Clean_Model'].dropna().unique() if str(m).strip().lower() != 'nan' and str(m).strip() != ""])
        else:
            model_options = []

        selected_model = st.selectbox("MODEL", options=[""] + model_options)
        filtered_by_model = filtered_by_make if not selected_model else filtered_by_make[filtered_by_make['Clean_Model'] == selected_model]
        
        if 'Year Range' in filtered_by_model.columns:
            year_options = sorted([str(y).strip() for y in filtered_by_model['Year Range'].dropna().unique() if str(y).strip().lower() != 'nan' and str(y).strip() != ""])
        else:
            year_options = []

        selected_year = st.selectbox("YEAR RANGE", options=[""] + year_options)

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
        st.markdown("<style>[data-testid=\"collapsedControl\"] { display: none !important; }</style>", unsafe_allow_html=True)

        results = st.session_state.results
        if len(results) == 1:
            record = results.iloc[0]
            st.subheader(f"{record.get('Make', '')} {record.get('Model', '')} | {record.get('Year Range', '')}")
            st.divider()

            st.subheader("General Details")
            general_cols = ['Vehicle Type', 'Fuel Type', 'Drivetrain', 'Engine', 'Engine Size', 'Engine Displacement (cc)', 'Axle Config']
            for col in general_cols:
                if col in record.index and is_valid(record[col]):
                    st.write(f"**{col}:** {record[col]}")
            st.divider()

            sections = {
                "🪫 BATTERY DETAILS": ["battery"], 
                "🏋️ JACKING POINTS & TORQUE": ["jack", "torque"], 
                "🔌 OBD LOCATION": ["obd", "odb"],
                "🅿️ HANDBRAKE RELEASE": ["electric handbrake"],
                "⚙️ GEAR NEUTRAL OVERRIDE": ["automatic gear"]
            }

            displayed = {'Make', 'Model', 'Year Range', 'Clean_Model'}.union(set(general_cols))

            for label, keywords in sections.items():
                with st.expander(label):
                    for col in record.index:
                        if any(k in col.lower() for k in keywords) and col not in displayed:
                            val = str(record[col])
                            st.markdown(f'<p class="result-header">{col}</p>', unsafe_allow_html=True)

                            if is_valid(val):
                                if "http" in val.lower() and ("photo" in col.lower() or val.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))):
                                    img_src = val
                                    if "drive.google.com" in val or "docs.google.com" in val:
                                        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', val) or re.search(r'id=([a-zA-Z0-9_-]+)', val)
                                        if match: img_src = f"https://drive.google.com/thumbnail?id={match.group(1)}&sz=w400"

                                    st.markdown(f'<a href="{val}" target="_blank"><img src="{img_src}" style="width:150px; height:150px; object-fit:cover; border-radius:8px; cursor:pointer; margin-bottom:10px;"></a>', unsafe_allow_html=True)
                                elif "http" in val.lower():
                                    st.link_button(f"🌐 View {col}", url=val)
                                else:
                                    st.write(val)
                            else:
                                st.write("*No data yet*")
                                if "photo" in col.lower():
                                    action = st.radio(f"Action for {col}:", ["Upload Photo", "Take New Photo"], key=f"radio_{col}")
                                    img_file = st.file_uploader(f"Choose file", type=['jpg', 'png', 'jpeg'], key=f"uploader_{col}") if action == "Upload Photo" else st.camera_input(f"Camera", key=f"camera_{col}")
                                    if img_file and st.button(f"Submit Photo for {col}", key=f"btn_{col}"):
                                        base64_str = base64.b64encode(img_file.getvalue()).decode('utf-8')
                                        requests.post(GOOGLE_SCRIPT_URL, json={"type": "photo", "make": record['Make'], "model": record['Model'], "column": col, "image": base64_str})
                                        st.success("Uploaded!")
                                else:
                                    with st.form(f"form_{col}_{record.name}"):
                                        new_val = st.text_input(f"Add info")
                                        if st.form_submit_button("Submit"):
                                            requests.post(GOOGLE_SCRIPT_URL, json={"type": "update", "make": record['Make'], "model": record['Model'], "column": col, "newValue": new_val})
                                            st.success("Submitted!")
                            displayed.add(col)

            with st.expander("🧩 OTHER SPECIFICATIONS"):
                found_other = False
                current_type = record.get('Vehicle Type', '')
                allowed_columns = sheet_columns.get(current_type, list(record.index))
                
                for col in allowed_columns:
                    if col in record.index and col not in displayed:
                        val = str(record[col])
                        st.markdown(f'<p class="result-header">{col}</p>', unsafe_allow_html=True)

                        if is_valid(val):
                            if "http" in val.lower() or "link" in col.lower() or "yuasa" in col.lower() or "dvla" in col.lower():
                                st.link_button(f"🌐 {col}", url=val, use_container_width=True)
                            else:
                                st.write(f"**{col}:** {val}")
                        else:
                            if "photo" in col.lower():
                                action = st.radio(f"Action for {col}:", ["Upload Photo", "Take New Photo"], key=f"radio_other_{col}")
                                img_file = st.file_uploader(f"Choose file", type=['jpg', 'png', 'jpeg'], key=f"uploader_other_{col}") if action == "Upload Photo" else st.camera_input(f"Camera", key=f"camera_other_{col}")
                                if img_file and st.button(f"Submit Photo for {col}", key=f"btn_other_{col}"):
                                    base64_str = base64.b64encode(img_file.getvalue()).decode('utf-8')
                                    requests.post(GOOGLE_SCRIPT_URL, json={"type": "photo", "make": record['Make'], "model": record['Model'], "column": col, "image": base64_str})
                                    st.success("Uploaded!")
                            else:
                                with st.form(f"form_other_{col}_{record.name}"):
                                    new_val = st.text_input(f"Add info")
                                    if st.form_submit_button("Submit"):
                                        requests.post(GOOGLE_SCRIPT_URL, json={"type": "update", "make": record['Make'], "model": record['Model'], "column": col, "newValue": new_val})
                                        st.success("Submitted!")
                        found_other = True

                if not found_other:
                    st.write("No additional information available.")

            with st.expander("➕ SUBMIT MISSING OR ADDITIONAL INFORMATION"):
                with st.form("general_missing_info_form", clear_on_submit=True):
                    st.write("Know something else about this vehicle? Provide text notes, attach a photo, or submit both below.")
                    extra_notes = st.text_area("Additional Info / Operational Notes", placeholder="e.g., AdBlue tank is behind driver panel.")
                    
                    photo_mode = st.radio("Attach a Photo?", ["No Photo", "Upload Photo From Device", "Take Photo with Camera"], key="gen_photo_mode")
                    attached_file = None
                    if photo_mode == "Upload Photo From Device":
                        attached_file = st.file_uploader("Choose image file", type=['jpg', 'png', 'jpeg'], key="gen_file_upload")
                    elif photo_mode == "Take Photo with Camera":
                        attached_file = st.camera_input("Capture image", key="gen_camera_input")
                        
                    if st.form_submit_button("SUBMIT SPECS UPDATE"):
                        if not extra_notes.strip() and not attached_file:
                            st.warning("Please type a note or provide an image before submitting.")
                        else:
                            base64_img = ""
                            if attached_file:
                                base64_img = base64.b64encode(attached_file.getvalue()).decode('utf-8')
                                
                            payload = {
                                "type": "general_missing_info",
                                "make": record.get('Make', ''),
                                "model": record.get('Model', ''),
                                "year": record.get('Year Range', ''),
                                "notes": extra_notes.strip(),
                                "image": base64_img
                            }
                            try:
                                response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
                                if response.status_code == 200:
                                    st.success("Information submitted successfully!")
                                else:
                                    st.error(f"Error: Status {response.status_code}")
                            except Exception as e:
                                st.error(f"Failed to transmit details: {e}")

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
