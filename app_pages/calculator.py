import streamlit as st
import pandas as pd
import re
from src.engine import (
    calculate_drawer_box, 
    calculate_cabinet_opening, 
    validate_inputs, 
    generate_svg, 
    float_to_fraction,
    format_dimension_pair,
    inches_to_mm,
    STANDARD_SLIDES,
    generate_csv_cutlist,
    generate_txt_summary
)
from src.ui_helpers import render_dimension_input
from src.storage import save_setup, list_setups, delete_setup, list_slides

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
def metric_card(title: str, val_inches: float, unit_system: str, color_theme: str = "blue"):
    theme_colors = {
        "blue": {"border": "#3b82f6", "text": "#38bdf8"},
        "amber": {"border": "#f59e0b", "text": "#fbbf24"},
        "green": {"border": "#10b981", "text": "#34d399"}
    }
    theme = theme_colors.get(color_theme, theme_colors["blue"])
    p_str, s_str = format_dimension_pair(val_inches, unit_system)
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
        <div style="font-size: 1.85rem; font-weight: 700; color: #f8fafc; line-height: 1.2;">{p_str}</div>
        <div style="font-size: 1.15rem; font-weight: 600; color: {theme['text']}; margin-top: 0.25rem;">{s_str}</div>
    </div>
    """

def inset_front_card(title: str, w_inches: float, h_inches: float, unit_system: str):
    is_metric = unit_system.startswith("Metric")
    w_p, _ = format_dimension_pair(w_inches, unit_system)
    h_p, _ = format_dimension_pair(h_inches, unit_system)
    
    other_sys = "Fractional Inches (\")" if is_metric else "Metric (mm)"
    w_s, _ = format_dimension_pair(w_inches, other_sys)
    h_s, _ = format_dimension_pair(h_inches, other_sys)

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
        <div style="font-size: 1.5rem; font-weight: 700; color: #f8fafc; line-height: 1.2;">{w_p} &times; {h_p}</div>
        <div style="font-size: 1.15rem; font-weight: 600; color: #34d399; margin-top: 0.25rem;">({w_s} &times; {h_s})</div>
    </div>
    """

# Sidebar Inputs & Initialization
st.sidebar.title("🔧 Parameters")

# Unit System Selection
if "unit_system" not in st.session_state:
    st.session_state.unit_system = "Fractional Inches (\")"

unit_system = st.sidebar.radio(
    "Unit System",
    options=["Fractional Inches (\")", "Metric (mm)"],
    key="unit_system",
    help="Select primary unit format across inputs, cards, diagrams, and report exports."
)

# Initialize session states if empty
if "project_name" not in st.session_state:
    st.session_state.project_name = "Drawer Box Project"
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
if "slide_type" not in st.session_state:
    st.session_state.slide_type = 'Blum Tandem (5/8" Wood)'

# Project / Configuration Name input
proj_name = st.sidebar.text_input(
    "Project / Drawer Name",
    key="project_name",
    help="Name your project to label exported reports and saved setups.",
    placeholder="e.g., Kitchen Base Drawer 1"
)

# Fetch slides from database
active_slides = list_slides()
slide_names = [s["name"] for s in active_slides]

if st.session_state.slide_type not in slide_names:
    if slide_names:
        st.session_state.slide_type = slide_names[0]

# Hardware slide profile selection
st.sidebar.subheader("Hardware Profile")
slide_name = st.sidebar.selectbox(
    "Slide Type",
    options=slide_names,
    key="slide_type"
)

selected_slide_cfg = next((s for s in active_slides if s["name"] == slide_name), None)

# Sidebar calculation mode selector
mode = st.sidebar.selectbox(
    "Calculation Mode", 
    ["Drawer Box Mode", "Carcass Mode"], 
    key="mode_selector"
)

# Render inputs reactive to chosen mode
if mode == "Drawer Box Mode":
    st.sidebar.subheader("Cabinet Opening Inputs")
    cab_w = render_dimension_input(
        "Cabinet Opening Width", 
        key="cab_w",
        default_val=20.0,
        min_val=1.0, 
        max_val=120.0, 
        sidebar=True,
        unit_system=unit_system
    )
    cab_h = render_dimension_input(
        "Cabinet Opening Height", 
        key="cab_h",
        default_val=6.0,
        min_val=1.0, 
        max_val=120.0, 
        sidebar=True,
        unit_system=unit_system
    )
    slide_len = st.sidebar.selectbox(
        "Slide Nominal Length (in)", 
        options=STANDARD_SLIDES, 
        key="slide_len"
    )
    
    # Run calculation
    results = calculate_drawer_box(cab_w, cab_h, slide_len, selected_slide_cfg)
    warnings = validate_inputs(cab_w, cab_h, slide_len, selected_slide_cfg)

else:  # Carcass Mode
    st.sidebar.subheader("Target Drawer Inputs")
    dr_w = render_dimension_input(
        "Target Drawer Box Width", 
        key="dr_w",
        default_val=19.625,
        min_val=1.0, 
        max_val=120.0, 
        sidebar=True,
        unit_system=unit_system
    )
    dr_h = render_dimension_input(
        "Target Drawer Box Height", 
        key="dr_h",
        default_val=5.0,
        min_val=1.0, 
        max_val=120.0, 
        sidebar=True,
        unit_system=unit_system
    )
    slide_len = st.sidebar.selectbox(
        "Slide Nominal Length (in)", 
        options=STANDARD_SLIDES, 
        key="slide_len"
    )
    
    # Run calculation
    results = calculate_cabinet_opening(dr_w, dr_h, slide_len, selected_slide_cfg)
    # Validate calculated cabinet sizes
    warnings = validate_inputs(results["cabinet_width"], results["cabinet_height"], slide_len, selected_slide_cfg)

# ----------------- MAIN LAYOUT -----------------

st.markdown('<div class="app-title">📐 Drawer Calculator</div>', unsafe_allow_html=True)
st.markdown(f'<div class="app-subtitle">Homelab tool dynamically configured for <strong>{slide_name}</strong> undermount drawer slides. Active Unit: <strong>{unit_system}</strong>.</div>', unsafe_allow_html=True)

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
            val_inches=results["drawer_width"],
            unit_system=unit_system,
            color_theme="amber"
        ), unsafe_allow_html=True)
        
    with m_col2:
        st.markdown(metric_card(
            title="Max Drawer Box Height",
            val_inches=results["drawer_height"],
            unit_system=unit_system,
            color_theme="amber"
        ), unsafe_allow_html=True)
        
    with m_col3:
        st.markdown(metric_card(
            title="Drawer Outside Depth",
            val_inches=results["drawer_depth"],
            unit_system=unit_system,
            color_theme="blue"
        ), unsafe_allow_html=True)
        
    with m_col4:
        st.markdown(inset_front_card(
            title="Inset Drawer Front",
            w_inches=results["inset_width"],
            h_inches=results["inset_height"],
            unit_system=unit_system
        ), unsafe_allow_html=True)

    # 3. Interactive SVG Expander
    with st.expander("🖼️ View Interactive 2D Cavity Overlay & Clearance Map", expanded=True):
        svg_code = generate_svg(results, selected_slide_cfg, project_name=proj_name, unit_system=unit_system)
        st.components.v1.html(svg_code, height=520, scrolling=False)
        st.caption(f"Figure: Wireframe diagram for '{proj_name}' showcasing Cabinet Cavity Opening (Dashed Blue), Inset Front Profile (Dashed Green), and Max Drawer Box Height clearance (Amber) with 5/8\" walls.")

    # 4. Copyable Markdown Summary Card
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.subheader(f"📋 Cut List & Workstation Summary: {proj_name}")
    
    # Gather specs
    w_cab = results["cabinet_width"]
    h_cab = results["cabinet_height"]
    w_dr = results["drawer_width"]
    h_dr = results["drawer_height"]
    d_dr = results["drawer_depth"]
    w_ins = results["inset_width"]
    h_ins = results["inset_height"]
    
    in_w = results["inside_width"]
    in_d = results["inside_depth"]
    bot_w = results.get("bottom_width", in_w + 0.5)
    bot_d = results.get("bottom_depth", in_d + 0.5)

    def pair_str(v):
        p, s = format_dimension_pair(v, unit_system)
        return f"{p}", f"{s}"

    w_cab_p, w_cab_s = pair_str(w_cab)
    h_cab_p, h_cab_s = pair_str(h_cab)
    w_dr_p, w_dr_s = pair_str(w_dr)
    h_dr_p, h_dr_s = pair_str(h_dr)
    d_dr_p, d_dr_s = pair_str(d_dr)
    w_ins_p, w_ins_s = pair_str(w_ins)
    h_ins_p, h_ins_s = pair_str(h_ins)
    in_w_p, in_w_s = pair_str(in_w)
    in_d_p, in_d_s = pair_str(in_d)
    bot_w_p, bot_w_s = pair_str(bot_w)
    bot_d_p, bot_d_s = pair_str(bot_d)

    min_dep_overlay = results.get("min_depth_overlay", d_dr + 0.65625)
    min_dep_inset = results.get("min_depth_inset", min_dep_overlay + 0.75)
    min_ov_p, min_ov_s = pair_str(min_dep_overlay)
    min_in_p, min_in_s = pair_str(min_dep_inset)

    p_header = "Primary Unit" if unit_system.startswith("Metric") else "Fractional Inch"
    s_header = "Fractional Inch" if unit_system.startswith("Metric") else "Metric Equivalent"

    summary_md = f"""
| Component | {p_header} | {s_header} | Qty | Notes / Woodworking Directions |
| :--- | :--- | :--- | :--- | :--- |
| **Cabinet Opening** | {w_cab_p} &times; {h_cab_p} | {w_cab_s} &times; {h_cab_s} | 1 | Opening space. Min depth: {min_ov_p} {min_ov_s} Overlay / {min_in_p} {min_in_s} Inset |
| **Drawer Box Outside** | {w_dr_p} &times; {h_dr_p} &times; {d_dr_p} | {w_dr_s} &times; {h_dr_s} &times; {d_dr_s} | 1 | Total external drawer dimensions (Max suggested height: {h_dr_p}). |
| **Side Panels** | {d_dr_p} &times; {h_dr_p} | {d_dr_s} &times; {h_dr_s} | 2 | Left and right outer drawer walls (Max suggested height: {h_dr_p}). |
| **Front & Back Panels** | {in_w_p} &times; {h_dr_p} | {in_w_s} &times; {h_dr_s} | 2 | Fit between sides. (Calculated width: Outside Width - 1.25"). |
| **Drawer Bottom Panel** | {bot_w_p} &times; {bot_d_p} | {bot_w_s} &times; {bot_d_s} | 1 | Housed in 1/4" dado grooves (Includes 1/2" total insertion depth). |
| **Inside Volume Space** | {in_w_p} &times; {in_d_p} | {in_w_s} &times; {in_d_s} | 1 | Maximum interior flat workspace clearance. |
| **Inset Front Reveal** | {w_ins_p} &times; {h_ins_p} | {w_ins_s} &times; {h_ins_s} | 1 | Calculated with uniform 3/32" reveal clearances. |
"""
    st.markdown(summary_md)
    
    if selected_slide_cfg:
        recess_p, recess_s = format_dimension_pair(selected_slide_cfg["bottom_recess"], unit_system)
        ext_p, ext_s = format_dimension_pair(selected_slide_cfg["extension_below"], unit_system)
        st.info(f"💡 **Undermount Fit Tip**: **{slide_name}** slides require the drawer bottom to be recessed **{recess_p} {recess_s}** from the bottom edge of the drawer sides, and the drawer sides to extend **{ext_p} {ext_s}** below the drawer bottom to cover the runner mechanisms.")

    # 5. Export / Download Section
    st.subheader("📥 Export Calculation Results")
    dl_col1, dl_col2, dl_col3 = st.columns(3)

    csv_data = generate_csv_cutlist(results, selected_slide_cfg, project_name=proj_name, unit_system=unit_system)
    txt_data = generate_txt_summary(results, selected_slide_cfg, project_name=proj_name, unit_system=unit_system)
    svg_code = generate_svg(results, selected_slide_cfg, project_name=proj_name, unit_system=unit_system)

    clean_proj_slug = re.sub(r'[^a-zA-Z0-9_\-]+', '_', proj_name.strip()).lower().strip('_')
    if not clean_proj_slug:
        clean_proj_slug = "drawer_project"
    file_prefix = f"{clean_proj_slug}_{int(results['cabinet_width'])}x{int(results['cabinet_height'])}"

    with dl_col1:
        st.download_button(
            label="📄 Cut List Summary (.txt)",
            data=txt_data,
            file_name=f"{file_prefix}_summary.txt",
            mime="text/plain",
            type="primary"
        )
    with dl_col2:
        st.download_button(
            label="📊 Spreadsheet Cut List (.csv)",
            data=csv_data,
            file_name=f"{file_prefix}_cutlist.csv",
            mime="text/csv",
            type="secondary"
        )
    with dl_col3:
        st.download_button(
            label="🖼️ 2D Overlay Diagram (.svg)",
            data=svg_code,
            file_name=f"{file_prefix}_diagram.svg",
            mime="image/svg+xml",
            type="secondary"
        )

with db_col:
    st.subheader("💾 Setup Management")
    
    # Form to save current setup
    with st.form("save_setup_form", clear_on_submit=False):
        st.write("Save Current Layout")
        setup_name = st.text_input("Configuration Name", value=proj_name, placeholder="e.g., Kitchen Base Drawer 1")
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
                    slide_len=results["drawer_depth"],
                    slide_name=slide_name
                )
                if saved:
                    st.session_state["project_name"] = setup_name.strip()
                    st.success(f"Saved configuration: '{setup_name.strip()}'")
                    st.rerun()
                else:
                    st.error("Failed to save configuration. A configuration with this name may already exist.")
                    
    # Callbacks for loading and deleting setups
    def load_setup_callback(setup_item):
        st.session_state["project_name"] = setup_item['name']
        if setup_item['mode'] == 'drawer_box_mode':
            st.session_state["mode_selector"] = "Drawer Box Mode"
            st.session_state["cab_w"] = setup_item['cabinet_width']
            st.session_state["cab_h"] = setup_item['cabinet_height']
            st.session_state["cab_w_text"] = float_to_fraction(setup_item['cabinet_width']).replace('"', '')
            st.session_state["cab_h_text"] = float_to_fraction(setup_item['cabinet_height']).replace('"', '')
        else:
            st.session_state["mode_selector"] = "Carcass Mode"
            st.session_state["dr_w"] = setup_item['drawer_width']
            st.session_state["dr_h"] = setup_item['drawer_height']
            st.session_state["dr_w_text"] = float_to_fraction(setup_item['drawer_width']).replace('"', '')
            st.session_state["dr_h_text"] = float_to_fraction(setup_item['drawer_height']).replace('"', '')
        
        st.session_state["slide_len"] = float(setup_item['slide_length'])
        st.session_state["slide_type"] = setup_item.get('slide_name', 'Blum Tandem (5/8" Wood)')

    def delete_setup_callback(setup_id):
        delete_setup(setup_id)

    # List and Load saved configurations
    st.write("Saved Projects")
    saved_setups = list_setups()
    
    if not saved_setups:
        st.info("No configurations saved yet.")
    else:
        for item in saved_setups:
            saved_slide_name = item.get('slide_name', 'Blum Tandem (5/8" Wood)')
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #2d2d30; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; background-color: #121214;">
                    <div style="font-weight: 600; color: #f8fafc; font-size: 0.95rem;">{item['name']}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.15rem;">
                        Mode: {'Box' if item['mode'] == 'drawer_box_mode' else 'Carcass'} | 
                        Slide: {int(item['slide_length'])}\" | 
                        Profile: {saved_slide_name}<br>
                        Cab: {float_to_fraction(item['cabinet_width'])} x {float_to_fraction(item['cabinet_height'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Small columns for action buttons
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    st.button("Load", key=f"load_{item['id']}", on_click=load_setup_callback, args=(item,))
                with btn_col2:
                    st.button("Delete", key=f"del_{item['id']}", on_click=delete_setup_callback, args=(item['id'],))
