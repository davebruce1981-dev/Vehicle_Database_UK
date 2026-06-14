import streamlit as st
import pandas as pd
import re
import requests

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Recovery Specs", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    h1, h2, h3, h4, p, label { color: #ffffff !important; }
    
    /* Main Search Button & Form Submit */
    div[data-testid="stVerticalBlock"] div.stButton > button,
    div[data-testid="stFormSubmitButton"] button { 
        background-color: #f6782a !important; 
        color: white !important; 
        width: 100%; 
        font-weight: bold; 
        border: none !important;
    }

    /* List View Result Buttons - Made Uniform */
    div[data-testid="element-container"] button div[data-testid="stMarkdownContainer"] p {
        font-weight: bold;
    }
    
    /* Target the result buttons specifically to keep them orange and uniform */
    div.stButton > button[key^="list_"] {
        background-color: #f6782a !important; 
        color: white !important; 
    }

    /* Distinct Style for the BACK Button */
    div.back-btn-container div[data-testid="stButton"] button {
        background-color: #333333 !important; 
        color: #ffffff !important; 
        border: 2px solid #555555 !important;
        font-weight: bold;
        width: 100%;
    }
    
    div.back-btn-container div[data-testid="stButton"] button:hover {
        border-color: #f6782a !important;
        color: #f6782a !important;
    }

    .result-header { font-size: 1.15em !important; color: #f6782a !important; font-weight: bold; margin-bottom: 2px; }
    
    /* Style Streamlit Expanders */
    .stExpander { border: 1px solid #333333 !important; background-color: #111111 !important; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1T7k-8tjbsZd0mpcfFzKpb3yisaxwLmOpoJeGQXXYc8M/gviz/tq?tqx=out:csv&sheet=Vehicle_Library"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

def main():
    col1, col2, col3 = st.columns([1, 4, 1]) 
    with col2:
        st.image("Recoveryspecs logo.jpeg", use_container_width=True)

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
        with st.expander("➕ Report a missing vehicle"):
            with st.form("new_vehicle_form", clear_on_submit=True):
                make = st.text_input("Make")
                model = st.text_input("Model")
                year = st.text_input("Year Range")
                details = st.text_area("Details")
                
                if st.form_submit_button("Send Request"):
                    url = "https://script.google.com/macros/s/AKfycbw1BzmjWIhqvgwEKbPzJdSz6JgpkDi11KnAM-IGcP8o495lnGWKFK6THoEigf8nXpjc/exec"
                    try:
                        payload = {"make": make, "model": model, "year": year, "details": details}
                        response = requests.post(url, json=payload, timeout=10)
                        if response.status_code == 200:
                            st.success("Request sent successfully!")
                        else:
                            st.error(f"Error: Server returned {response.status_code}")
                    except Exception as e:
                        st.error(f"Connection failed: {str(e)}")
    else:
        results = st.session_state.results
        if len(results) == 1:
            st.subheader("Vehicle Details")
            record = results.iloc[0]
            
            def find_col(name):
                for c in record.index:
                    if c.strip().lower() == name.strip().lower(): return c
                return None

            make_c = find_col("Make")
            model_c = find_col("Model")
            year_c = find_col("Year Range")
            fuel_c = find_col("Fuel Type")
            drive_c = find_col("Drivetrain")

            brand = str(record[make_c]) if make_c else ""
            model_name = str(record[model_c]) if model_c else ""
            st.markdown(f"## {brand} {model_name}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**YEAR RANGE:** {record[year_c] if year_c else 'N/A'}")
                st.markdown(f"**FUEL TYPE:** {record[fuel_c] if fuel_c else 'N/A'}")
            with c2:
                st.markdown(f"**DRIVETRAIN:** {record[drive_c] if drive_c else 'N/A'}")
            
            st.divider()

            # Updated sections with your new specific column names
            sections = {
                "🪫 BATTERY DETAILS": ["battery", "hybrid", "voltage", "12v", "battery comments"],
                "🏋️ JACKING POINTS": ["jack", "jacking", "lift", "point", "torque", "jacking comments"],
                "🔌 OBD LOCATION": ["obd", "odb", "diagnostic", "port", "odb comments"]
            }

            displayed_cols = {make_c, model_c, year_c, fuel_c, drive_c, 'Clean_Model', 'Model', 'Make'}

            for label, keywords in sections.items():
                matched_cols = [c for c in record.index if any(kw in c.lower() for kw in keywords) and c not in displayed_cols]
                with st.expander(label):
                    if matched_cols:
                        for col in matched_cols:
                            st.markdown(f'<p class="result-header">{col}</p>', unsafe_allow_html=True)
                            st.write(str(record[col]))
                            displayed_cols.add(col)
                    else:
                        st.info("No specific data found for this category.")

            other_cols = [c for c in record.index if c not in displayed_cols]
            if other_cols:
                with st.expander("🔍 ADDITIONAL SPECIFICATIONS"):
                    for col in other_cols:
                        st.markdown(f'<p class="result-header">{col}</p>', unsafe_allow_html=True)
                        st.write(str(record[col]))
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            with st.container(border=False):
                st.markdown('<div class="back-btn-container">', unsafe_allow_html=True)
                if st.button("⬅ Back to Search", key="back_from_details"):
                    st.session_state.show_results = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.subheader(f"Found {len(results)} Results")
            for idx, row in results.iterrows():
                if st.button(f"{row['Make']} | {row['Model']} | {row['Year Range']}", key=f"list_{idx}", use_container_width=True):
                    st.session_state.results = results.loc[[idx]]
                    st.rerun()
            
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            with st.container(border=False):
                st.markdown('<div class="back-btn-container">', unsafe_allow_html=True)
                if st.button("⬅ Back to Search", key="back_from_list"):
                    st.session_state.show_results = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
