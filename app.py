import streamlit as st

# Configure global page parameters once at the entrypoint
st.set_page_config(
    page_title="Drawer Calculator", 
    page_icon="📐", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Define pages for multi-page navigation
intro_page = st.Page("app_pages/intro.py", title="About the Tool", icon=":material/info:")
calc_page = st.Page("app_pages/calculator.py", title="Drawer Calculator", icon=":material/calculate:")
joint_page = st.Page("app_pages/joint_layout.py", title="Joint Spacing Layout", icon=":material/grid_view:")
slides_page = st.Page("app_pages/slides.py", title="Slide Configurations", icon=":material/tune:")

# Initialize navigation structure
pg = st.navigation([intro_page, calc_page, joint_page, slides_page])

# Render selected page
pg.run()
