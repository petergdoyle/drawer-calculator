import streamlit as st
import pandas as pd
from src.engine import (
    calculate_drawer_box, 
    calculate_cabinet_opening, 
    validate_inputs, 
    generate_svg, 
    float_to_fraction,
    STANDARD_SLIDES
)
from src.storage import save_setup, list_setups, delete_setup

# Page Setup
st.set_page_config(
    page_title="Drawer Calculator", 
    page_icon="📐", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom Style Injections
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [data-testid="stSidebar"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Sleek gradient page title */
    .app-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .app-subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Warning container design */
    .warning-box {
        background-color: #2a1b18;
        border-left: 5px solid #ef4444;
        border-radius: 8px;
        padding: 1rem;
        color: #fca5a5;
        margin-bottom: 1.5rem;
        font-size: 0.95rem;
    }
    
    /* Custom divider line */
    .divider {
        height: 1px;
        background-color: #2d2d30;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Metrics card builders
def metric_card(title: str, value_decimal: float, value_fraction: str, color_theme: str = "blue"):
    theme_colors = {
        "blue": {"border": "#3b82f6", "text": "#38bdf8"},
        "amber": {"border": "#f59e0b", "text": "#fbbf24"},
        "green": {"border": "#10b981", "text": "#34d399"}
    }
    theme = theme_colors.get(color_theme, theme_colors["blue"])
    return f"""
    <div style="
        background-color: #1a1a24;
        border: 1px solid #2d2d3d;
        border-top: 4px solid {theme['border']};
        border-radius: 12px;
        padding: 1.25rem 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        text-align: center;
        margin-bottom: 1rem;
    ">
        <div style="font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">{title}</div>
        <div style="font-size: 1.85rem; font-weight: 700; color: #f8fafc; line-height: 1.2;">{value_decimal:.3f}"</div>
        <div style="font-size: 1.15rem; font-weight: 600; color: {theme['text']}; margin-top: 0.25rem;">{value_fraction}</div>
    </div>
    """

def inset_front_card(title: str, w_dec: float, w_frac: str, h_dec: float, h_frac: str):
    return f"""
    <div style="
        background-color: #1a1a24;
        border: 1px solid #2d2d3d;
        border-top: 4px solid #10b981;
        border-radius: 12px;
        padding: 1.25rem 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        text-align: center;
        margin-bottom: 1rem;
    ">
        <div style="font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">{title}</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: #f8fafc; line-height: 1.2;">{w_dec:.3f}" &times; {h_dec:.3f}"</div>
        <div style="font-size: 1.15rem; font-weight: 600; color: #34d399; margin-top: 0.25rem;">{w_frac} &times; {h_frac}</div>
    </div>
    """

# Sidebar Inputs & Initialization
st.sidebar.title("🔧 Parameters")

# Initialize session states if empty
if "mode_selector" not in st.session_state:
    st.session_state.mode_selector = "Drawer Box Mode"
if "cab_w" not in st.session_state:
    st.session_state.cab_w = 20.0
if "cab_h" not in st.session_state:
    st.session_state.cab_h = 6.0
if "dr_w" not in st.session_state:
    st.session_state.dr_w = 19.625
if "dr_h" not in st.session_state:
    st.session_state.dr_h = 5.0
if "slide_len" not in st.session_state:
    st.session_state.slide_len = 21.0

# Sidebar calculation mode selector
mode = st.sidebar.selectbox(
    "Calculation Mode", 
    ["Drawer Box Mode", "Carcass Mode"], 
    key="mode_selector"
)

# Render inputs reactive to chosen mode
if mode == "Drawer Box Mode":
    st.sidebar.subheader("Cabinet Opening Inputs")
    cab_w = st.sidebar.number_input(
        "Cabinet Opening Width (in)", 
        min_value=1.0, 
        max_value=120.0, 
        step=0.125, 
        key="cab_w"
    )
    cab_h = st.sidebar.number_input(
        "Cabinet Opening Height (in)", 
        min_value=1.0, 
        max_value=120.0, 
        step=0.125, 
        key="cab_h"
    )
    slide_len = st.sidebar.selectbox(
        "Slide Nominal Length (in)", 
        options=STANDARD_SLIDES, 
        key="slide_len"
    )
    
    # Run calculation
    results = calculate_drawer_box(cab_w, cab_h, slide_len)
    warnings = validate_inputs(cab_w, cab_h, slide_len)

else:  # Carcass Mode
    st.sidebar.subheader("Target Drawer Inputs")
    dr_w = st.sidebar.number_input(
        "Target Drawer Box Width (in)", 
        min_value=1.0, 
        max_value=120.0, 
        step=0.125, 
        key="dr_w"
    )
    dr_h = st.sidebar.number_input(
        "Target Drawer Box Height (in)", 
        min_value=1.0, 
        max_value=120.0, 
        step=0.125, 
        key="dr_h"
    )
    slide_len = st.sidebar.selectbox(
        "Slide Nominal Length (in)", 
        options=STANDARD_SLIDES, 
        key="slide_len"
    )
    
    # Run calculation
    results = calculate_cabinet_opening(dr_w, dr_h, slide_len)
    # Validate calculated cabinet sizes
    warnings = validate_inputs(results["cabinet_width"], results["cabinet_height"], slide_len)

# ----------------- MAIN LAYOUT -----------------

st.markdown('<div class="app-title">📐 Drawer Calculator</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Homelab tool for Blum Tandem undermount drawer slides and carcass dimensions.</div>', unsafe_allow_html=True)

# Split page into main content (Left) and persistence column (Right)
main_col, db_col = st.columns([7, 3])

with main_col:
    # 1. Clearances warnings block if any
    if warnings:
        warnings_html = "".join([f"<li>⚠️ {w}</li>" for w in warnings])
        st.markdown(f'<div class="warning-box"><strong style="color:#ef4444;">Safety Clearances & Physical Constraints Check:</strong><ul style="margin: 0.5rem 0 0 0; padding-left: 1.25rem;">{warnings_html}</ul></div>', unsafe_allow_html=True)
    
    # 2. Key Metrics Row
    st.subheader("📊 Calculation Results")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    with m_col1:
        st.markdown(metric_card(
            title="Drawer Box Width",
            value_decimal=results["drawer_width"],
            value_fraction=float_to_fraction(results["drawer_width"]),
            color_theme="amber"
        ), unsafe_allow_html=True)
        
    with m_col2:
        st.markdown(metric_card(
            title="Drawer Box Height",
            value_decimal=results["drawer_height"],
            value_fraction=float_to_fraction(results["drawer_height"]),
            color_theme="amber"
        ), unsafe_allow_html=True)
        
    with m_col3:
        st.markdown(metric_card(
            title="Drawer Outside Depth",
            value_decimal=results["drawer_depth"],
            value_fraction=float_to_fraction(results["drawer_depth"]),
            color_theme="blue"
        ), unsafe_allow_html=True)
        
    with m_col4:
        st.markdown(inset_front_card(
            title="Inset Drawer Front",
            w_dec=results["inset_width"],
            w_frac=float_to_fraction(results["inset_width"]),
            h_dec=results["inset_height"],
            h_frac=float_to_fraction(results["inset_height"])
        ), unsafe_allow_html=True)

    # 3. Interactive SVG Expander
    with st.expander("🖼️ View Interactive 2D Cavity Overlay & Clearance Map", expanded=True):
        svg_code = generate_svg(results)
        st.components.v1.html(svg_code, height=520, scrolling=False)
        st.caption("Figure: Wireframe diagram showcasing Cabinet Cavity Opening (Dashed Blue), Inset Front Profile (Dashed Green), and Drawer Box Outside dimensions (Amber) with 5/8\" walls.")

    # 4. Copyable Markdown Summary Card
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.subheader("📋 Cut List & Workstation Summary")
    
    # Gather specs
    w_cab = results["cabinet_width"]
    h_cab = results["cabinet_height"]
    w_dr = results["drawer_width"]
    h_dr = results["drawer_height"]
    d_dr = results["drawer_depth"]
    w_ins = results["inset_width"]
    h_ins = results["inset_height"]
    
    # Inside pieces measurements (assume front & back pieces captured between side panels)
    in_w = results["inside_width"]
    in_d = results["inside_depth"]
    
    w_cab_str = float_to_fraction(w_cab)
    h_cab_str = float_to_fraction(h_cab)
    w_dr_str = float_to_fraction(w_dr)
    h_dr_str = float_to_fraction(h_dr)
    d_dr_str = float_to_fraction(d_dr)
    w_ins_str = float_to_fraction(w_ins)
    h_ins_str = float_to_fraction(h_ins)
    in_w_str = float_to_fraction(in_w)
    in_d_str = float_to_fraction(in_d)

    summary_md = f"""
| Component | Metric (in) | Fractional | Qty | Notes / Woodworking Directions |
| :--- | :--- | :--- | :--- | :--- |
| **Cabinet Opening** | {w_cab:.3f}" &times; {h_cab:.3f}" | {w_cab_str} &times; {h_cab_str} | 1 | Required carcass opening size. Min depth: {d_dr + 0.125:.3f}" |
| **Drawer Box Outside** | {w_dr:.3f}" &times; {h_dr:.3f}" &times; {d_dr:.3f}" | {w_dr_str} &times; {h_dr_str} &times; {d_dr_str} | 1 | Total external drawer dimensions. |
| **Side Panels** | {d_dr:.3f}" &times; {h_dr:.3f}" | {d_dr_str} &times; {h_dr_str} | 2 | Left and right outer drawer walls (5/8" thickness). |
| **Front & Back Panels** | {in_w:.3f}" &times; {h_dr:.3f}" | {in_w_str} &times; {h_dr_str} | 2 | Fit between sides. (Calculated width: Outside Width - 1.25"). |
| **Inside Volume Space** | {in_w:.3f}" &times; {in_d:.3f}" | {in_w_str} &times; {in_d_str} | 1 | Maximum interior flat workspace clearance. |
| **Inset Front Reveal** | {w_ins:.3f}" &times; {h_ins:.3f}" | {w_ins_str} &times; {h_ins_str} | 1 | Calculated with uniform 3/32" reveal clearances. |
"""
    st.markdown(summary_md)
    st.info("💡 **Undermount Fit Tip**: Blum Tandem slides require the drawer bottom to be recessed **1/2\" (13mm)** from the bottom edge of the drawer sides, and the drawer sides to extend **7/32\" (5.5mm)** below the drawer bottom to cover the runner mechanisms.")

with db_col:
    st.subheader("💾 Setup Management")
    
    # Form to save current setup
    with st.form("save_setup_form", clear_on_submit=True):
        st.write("Save Current Layout")
        setup_name = st.text_input("Configuration Name", placeholder="e.g., Kitchen Base Drawer 1")
        submit_save = st.form_submit_button("Save Configuration")
        
        if submit_save:
            if not setup_name.strip():
                st.error("Please enter a valid configuration name.")
            else:
                saved = save_setup(
                    name=setup_name.strip(),
                    mode=results["mode"],
                    cabinet_w=results["cabinet_width"],
                    cabinet_h=results["cabinet_height"],
                    drawer_w=results["drawer_width"],
                    drawer_h=results["drawer_height"],
                    slide_len=results["drawer_depth"]
                )
                if saved:
                    st.success(f"Saved configuration: '{setup_name.strip()}'")
                else:
                    st.error("Failed to save configuration. A configuration with this name may already exist.")
                    
    # List and Load saved configurations
    st.write("Saved Projects")
    saved_setups = list_setups()
    
    if not saved_setups:
        st.info("No configurations saved yet.")
    else:
        for item in saved_setups:
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #2d2d30; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; background-color: #121214;">
                    <div style="font-weight: 600; color: #f8fafc; font-size: 0.95rem;">{item['name']}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.15rem;">
                        Mode: {'Box' if item['mode'] == 'drawer_box_mode' else 'Carcass'} | 
                        Slide: {int(item['slide_length'])}\" | 
                        Cab: {float_to_fraction(item['cabinet_width'])} x {float_to_fraction(item['cabinet_height'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Small columns for action buttons
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("Load", key=f"load_{item['id']}"):
                        # Load data into session states
                        if item['mode'] == 'drawer_box_mode':
                            st.session_state.mode_selector = "Drawer Box Mode"
                            st.session_state.cab_w = item['cabinet_width']
                            st.session_state.cab_h = item['cabinet_height']
                        else:
                            st.session_state.mode_selector = "Carcass Mode"
                            st.session_state.dr_w = item['drawer_width']
                            st.session_state.dr_h = item['drawer_height']
                        
                        st.session_state.slide_len = item['slide_length']
                        st.rerun()
                        
                with btn_col2:
                    if st.button("Delete", key=f"del_{item['id']}"):
                        if delete_setup(item['id']):
                            st.warning(f"Deleted '{item['name']}'")
                            st.rerun()
                        else:
                            st.error("Failed to delete setup.")
