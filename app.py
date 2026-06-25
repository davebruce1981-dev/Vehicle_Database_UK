import streamlit as st
import pandas as pd

# --- DATA FETCHING (The "Backbone" of your app) ---
@st.cache_data(ttl=600)
def load_data():
    # Use the link from your "Publish to web" step
    url = "PASTE_YOUR_LINK_HERE" 
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return pd.DataFrame()

# --- MAIN APP ---
def main():
    st.title("Recovery Specs")
    df = load_data()
    
    if df.empty:
        st.stop() # Stop here if no data

    # Dropdowns
    make = st.selectbox("MAKE", [""] + sorted(df['Make'].dropna().unique().tolist()))
    
    filtered_df = df[df['Make'] == make] if make else df
    
    model = st.selectbox("MODEL", [""] + sorted(filtered_df['Model'].dropna().unique().tolist()))
    
    # --- YOUR NEW FEATURE HERE ---
    # We wrap your new feature in a 'try/except' block so it doesn't break the whole app
    try:
        # Example: if you were adding a "Battery Location" display
        if model:
            specs = df[(df['Make'] == make) & (df['Model'] == model)]
            st.write("### Specs")
            st.write(specs[['Year Range', 'Fuel Type', 'Drivetrain']])
    except Exception as e:
        st.warning("New feature is currently disabled due to a small error.")
        print(f"Feature error: {e}")

if __name__ == "__main__":
    main()
