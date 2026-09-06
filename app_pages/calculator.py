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
if "material_thickness" not in st.session_state:
    st.session_state.material_thickness = 0.625
if "joint_type" not in st.session_state:
    st.session_state.joint_type = 'Butt Joint (Dominos / Dowels)'
if "bottom_thickness" not in st.session_state:
    st.session_state.bottom_thickness = 0.25
if "dado_depth" not in st.session_state:
    st.session_state.dado_depth = 0.375

# Fetch slides from database
active_slides = list_slides()
slide_names = [s["name"] for s in active_slides]

if st.session_state.slide_type not in slide_names:
    if slide_names:
        st.session_state.slide_type = slide_names[0]

# Snapshot helper for tracking unsaved modifications
def get_current_snapshot():
    return {
        'name': st.session_state.get('project_name', 'Drawer Box Project'),
        'mode': st.session_state.get('mode_selector', 'Drawer Box Mode'),
        'cab_w': float(st.session_state.get('cab_w', 20.0)),
        'cab_h': float(st.session_state.get('cab_h', 6.0)),
        'dr_w': float(st.session_state.get('dr_w', 19.625)),
        'dr_h': float(st.session_state.get('dr_h', 5.0)),
        'slide_len': float(st.session_state.get('slide_len', 21.0)),
        'slide_type': st.session_state.get('slide_type', slide_names[0] if slide_names else ''),
        'material_thickness': float(st.session_state.get('material_thickness', 0.625)),
        'joint_type': st.session_state.get('joint_type', 'Butt Joint (Dominos / Dowels)'),
        'bottom_thickness': float(st.session_state.get('bottom_thickness', 0.25)),
        'dado_depth': float(st.session_state.get('dado_depth', 0.375))
    }

if "saved_snapshot" not in st.session_state:
    st.session_state.saved_snapshot = get_current_snapshot()

def reset_to_new_project():
    st.session_state["project_name"] = "New Drawer Project"
    st.session_state["setup_name_input"] = "New Drawer Project"
    st.session_state["mode_selector"] = "Drawer Box Mode"
    st.session_state["cab_w"] = 20.0
    st.session_state["cab_h"] = 6.0
    st.session_state["cab_w_text"] = "20"
    st.session_state["cab_h_text"] = "6"
    st.session_state["dr_w"] = 19.625
    st.session_state["dr_h"] = 5.0
    st.session_state["dr_w_text"] = "19 5/8"
    st.session_state["dr_h_text"] = "5"
    st.session_state["slide_len"] = 21.0
    if slide_names:
        st.session_state["slide_type"] = slide_names[0]
    st.session_state["material_thickness"] = 0.625
    st.session_state["material_thickness_text"] = "5/8"
    st.session_state["joint_type"] = 'Butt Joint (Dominos / Dowels)'
    st.session_state["bottom_thickness"] = 0.25
    st.session_state["bottom_thickness_text"] = "1/4"
    st.session_state["dado_depth"] = 0.375
    st.session_state["dado_depth_text"] = "3/8"
    st.session_state["pending_action"] = None
    st.session_state.saved_snapshot = get_current_snapshot()

def handle_save_setup_callback():
    name_to_save = st.session_state.get("setup_name_input", "").strip()
    if not name_to_save:
        st.session_state["save_error_msg"] = "Please enter a valid configuration name."
        st.session_state["save_success_msg"] = None
        return
    
    current_mode = st.session_state.get("mode_selector", "Drawer Box Mode")
    mode_str = "drawer_box_mode" if current_mode == "Drawer Box Mode" else "carcass_mode"
    
    b_thick = float(st.session_state.get("bottom_thickness", 0.25))
    d_depth = float(st.session_state.get("dado_depth", 0.375))
    
    saved = save_setup(
        name=name_to_save,
        mode=mode_str,
        cabinet_w=float(st.session_state.get("cab_w", 20.0)),
        cabinet_h=float(st.session_state.get("cab_h", 6.0)),
        drawer_w=float(st.session_state.get("dr_w", 19.625)),
        drawer_h=float(st.session_state.get("dr_h", 5.0)),
        slide_len=float(st.session_state.get("slide_len", 21.0)),
        slide_name=st.session_state.get("slide_type", "Blum Tandem (5/8\" Wood)"),
        material_thickness=float(st.session_state.get("material_thickness", 0.625)),
        joint_type=st.session_state.get("joint_type", "Butt Joint (Dominos / Dowels)"),
        bottom_thickness=b_thick,
        dado_depth=d_depth
    )
    
    if saved:
        st.session_state["project_name"] = name_to_save
        st.session_state["setup_name_input"] = name_to_save
        st.session_state["pending_action"] = None
        st.session_state["save_success_msg"] = f"Saved configuration: '{name_to_save}'"
        st.session_state["save_error_msg"] = None
        st.session_state.saved_snapshot = {
            'name': name_to_save,
            'mode': current_mode,
            'cab_w': float(st.session_state.get('cab_w', 20.0)),
            'cab_h': float(st.session_state.get('cab_h', 6.0)),
            'dr_w': float(st.session_state.get('dr_w', 19.625)),
            'dr_h': float(st.session_state.get('dr_h', 5.0)),
            'slide_len': float(st.session_state.get('slide_len', 21.0)),
            'slide_type': st.session_state.get('slide_type', ''),
            'material_thickness': float(st.session_state.get('material_thickness', 0.625)),
            'joint_type': st.session_state.get('joint_type', ''),
            'bottom_thickness': b_thick,
            'dado_depth': d_depth
        }
    else:
        st.session_state["save_error_msg"] = f"Failed to save configuration '{name_to_save}'. A configuration with this name may already exist."
        st.session_state["save_success_msg"] = None

def load_setup_callback(setup_item):
    st.session_state["project_name"] = setup_item['name']
    st.session_state["setup_name_input"] = setup_item['name']
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
    
    m_thick = float(setup_item.get('material_thickness', 0.625))
    st.session_state["material_thickness"] = m_thick
    st.session_state["material_thickness_text"] = float_to_fraction(m_thick).replace('"', '')
    st.session_state["joint_type"] = setup_item.get('joint_type', 'Butt Joint (Dominos / Dowels)')
    
    b_thick = float(setup_item.get('bottom_thickness', 0.25))
    st.session_state["bottom_thickness"] = b_thick
    st.session_state["bottom_thickness_text"] = float_to_fraction(b_thick).replace('"', '')
    
    d_depth = float(setup_item.get('dado_depth', 0.375))
    st.session_state["dado_depth"] = d_depth
    st.session_state["dado_depth_text"] = float_to_fraction(d_depth).replace('"', '')
    
    st.session_state["pending_action"] = None
    st.session_state.saved_snapshot = {
        'name': setup_item['name'],
        'mode': 'Drawer Box Mode' if setup_item['mode'] == 'drawer_box_mode' else 'Carcass Mode',
        'cab_w': float(setup_item['cabinet_width']),
        'cab_h': float(setup_item['cabinet_height']),
        'dr_w': float(setup_item['drawer_width']),
        'dr_h': float(setup_item['drawer_height']),
        'slide_len': float(setup_item['slide_length']),
        'slide_type': setup_item.get('slide_name', 'Blum Tandem (5/8" Wood)'),
        'material_thickness': m_thick,
        'joint_type': setup_item.get('joint_type', 'Butt Joint (Dominos / Dowels)'),
        'bottom_thickness': b_thick,
        'dado_depth': d_depth
    }

def delete_setup_callback(setup_id):
    delete_setup(setup_id)

# New Project Button at top of sidebar
if st.sidebar.button("➕ Create New Project", type="primary", use_container_width=True):
    current_snap = get_current_snapshot()
    if current_snap != st.session_state.saved_snapshot:
        st.session_state["pending_action"] = "new_project"
    else:
        reset_to_new_project()

# Project / Configuration Name input
proj_name = st.sidebar.text_input(
    "Project / Drawer Name",
    key="project_name",
    help="Unique label for this project configuration. Used in titles, exported reports (.txt, .csv, .svg), and database setups.",
    placeholder="e.g., Kitchen Base Drawer 1"
)

# Hardware slide profile selection
st.sidebar.subheader("Hardware Profile")
slide_name = st.sidebar.selectbox(
    "Slide Type",
    options=slide_names,
    key="slide_type",
    help="Select hardware slide profile (e.g. Blum Tandem 563H for 5/8\" wood, 569 for 3/4\" wood, or custom runner). Determines side & height clearance tolerances and maximum wood thickness ratings."
)

selected_slide_cfg = next((s for s in active_slides if s["name"] == slide_name), None)

# Drawer Material & Joinery Specs
st.sidebar.subheader("Drawer Material Specs")
mat_thick = render_dimension_input(
    "Drawer Wood Thickness",
    key="material_thickness",
    default_val=0.625,
    min_val=0.25,
    max_val=1.5,
    help_text="Thickness of side, front, and back drawer box wood walls (e.g., 5/8\", 1/2\", 3/4\", 15 mm). Validated against slide runner maximum thickness.",
    sidebar=True,
    unit_system=unit_system
)

joint_options = [
    "Butt Joint (Dominos / Dowels)",
    "Butt Joint (Pocket Holes)",
    "Butt Joint (Screws / Dowels)",
    "Miter Joint",
    "Dovetail Joint",
    "Box Joint",
    "Dado Butt Joint"
]
if st.session_state.joint_type not in joint_options:
    st.session_state.joint_type = joint_options[0]

joint_type = st.sidebar.selectbox(
    "Box Joinery Type",
    options=joint_options,
    key="joint_type",
    help="Corner joinery method. Butt joints subtract 2x material thickness for front/back panels; Miter, Dovetail, and Box joints cut front/back panels to full exterior drawer width."
)

# Bottom Panel Specs
st.sidebar.subheader("Bottom Panel Specs")
bot_thick = render_dimension_input(
    "Bottom Panel Thickness",
    key="bottom_thickness",
    default_val=0.25,
    min_val=0.125,
    max_val=0.75,
    help_text="Thickness of drawer bottom panel board (e.g., 1/4\", 3/8\", 1/2\", 6 mm).",
    sidebar=True,
    unit_system=unit_system
)

dado_d = render_dimension_input(
    "Dado Groove Depth",
    key="dado_depth",
    default_val=0.375,
    min_val=0.125,
    max_val=0.75,
    help_text="Insertion depth of groove cut into drawer sides, front, and back (default 3/8\" on 4 sides, adds 3/4\" total to interior width & depth for bottom cut size).",
    sidebar=True,
    unit_system=unit_system
)

# Sidebar calculation mode selector
mode = st.sidebar.selectbox(
    "Calculation Mode", 
    ["Drawer Box Mode", "Carcass Mode"], 
    key="mode_selector",
    help="Select calculation direction:\n• Drawer Box Mode: Calculate recommended drawer box size from cabinet cavity opening.\n• Carcass Mode: Calculate required cabinet cavity opening from target drawer box size."
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
        help_text="Clear internal opening width of the cabinet cavity between side walls (e.g., 20\", 20 1/2\", 508 mm).",
        sidebar=True,
        unit_system=unit_system
    )
    cab_h = render_dimension_input(
        "Cabinet Opening Height", 
        key="cab_h",
        default_val=6.0,
        min_val=1.0, 
        max_val=120.0, 
        help_text="Clear internal opening height of the cabinet cavity or face frame (e.g., 6\", 6 1/4\", 152 mm).",
        sidebar=True,
        unit_system=unit_system
    )
    slide_len = st.sidebar.selectbox(
        "Slide Nominal Length (in)", 
        options=STANDARD_SLIDES, 
        key="slide_len",
        help="Standard nominal runner length (e.g., 9\", 12\", 15\", 18\", 21\", 24\", 27\", 30\"). Determines drawer box depth and minimum carcass depth."
    )
    
    # Run calculation
    results = calculate_drawer_box(
        cab_w, cab_h, slide_len, selected_slide_cfg,
        material_thickness=mat_thick, joint_type=joint_type,
        bottom_thickness=bot_thick, dado_depth=dado_d
    )
    warnings = validate_inputs(cab_w, cab_h, slide_len, selected_slide_cfg, material_thickness=mat_thick)

else:  # Carcass Mode
    st.sidebar.subheader("Target Drawer Inputs")
    dr_w = render_dimension_input(
        "Target Drawer Box Width", 
        key="dr_w",
        default_val=19.625,
        min_val=1.0, 
        max_val=120.0, 
        help_text="Target exterior width of assembled drawer box (e.g., 19 5/8\", 19.625\", 500 mm).",
        sidebar=True,
        unit_system=unit_system
    )
    dr_h = render_dimension_input(
        "Target Drawer Box Height", 
        key="dr_h",
        default_val=5.0,
        min_val=1.0, 
        max_val=120.0, 
        help_text="Target exterior height of drawer box side walls (e.g., 5\", 5.25\", 130 mm).",
        sidebar=True,
        unit_system=unit_system
    )
    slide_len = st.sidebar.selectbox(
        "Slide Nominal Length (in)", 
        options=STANDARD_SLIDES, 
        key="slide_len",
        help="Standard nominal runner length (e.g., 9\", 12\", 15\", 18\", 21\", 24\", 27\", 30\"). Determines drawer box depth and minimum carcass depth."
    )
    
    # Run calculation
    results = calculate_cabinet_opening(
        dr_w, dr_h, slide_len, selected_slide_cfg,
        material_thickness=mat_thick, joint_type=joint_type,
        bottom_thickness=bot_thick, dado_depth=dado_d
    )
    # Validate calculated cabinet sizes
    warnings = validate_inputs(results["cabinet_width"], results["cabinet_height"], slide_len, selected_slide_cfg, material_thickness=mat_thick)

# Check dirty state after all inputs rendered
current_snap = get_current_snapshot()
is_dirty = (current_snap != st.session_state.saved_snapshot)

# ----------------- MAIN LAYOUT -----------------

st.markdown('<div class="app-title">📐 Drawer Calculator</div>', unsafe_allow_html=True)
st.markdown(f'<div class="app-subtitle">Homelab tool dynamically configured for <strong>{slide_name}</strong> undermount drawer slides. Active Unit: <strong>{unit_system}</strong>.</div>', unsafe_allow_html=True)

# Prompt for confirmation if user requested new project with unsaved changes
if st.session_state.get("pending_action") == "new_project":
    st.warning(f"⚠️ **Unsaved Changes Warning**: You have modified parameters in project **'{st.session_state.project_name}'**. Would you like to save your changes first?")
    confirm_col1, confirm_col2, confirm_col3 = st.columns(3)
    with confirm_col1:
        if st.button("🗑️ Discard & Create New", type="primary"):
            reset_to_new_project()
    with confirm_col2:
        if st.button("❌ Keep Editing"):
            st.session_state["pending_action"] = None
            st.rerun()

elif is_dirty:
    st.info(f"✏️ **Unsaved Changes**: You have modified parameters in **'{st.session_state.project_name}'**. Don't forget to save your project in Setup Management!")

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
        st.caption(f"Figure: Wireframe diagram for '{proj_name}' showcasing Cabinet Cavity Opening (Dashed Blue), Inset Front Profile (Dashed Green), and Max Drawer Box Height clearance (Amber) with {float_to_fraction(mat_thick)} walls.")

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
    fb_cut_w = results.get("front_back_cut_width", in_w)
    bot_w = results.get("bottom_width", in_w + 2 * dado_d)
    bot_d = results.get("bottom_depth", in_d + 2 * dado_d)

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
    fb_cut_p, fb_cut_s = pair_str(fb_cut_w)
    bot_w_p, bot_w_s = pair_str(bot_w)
    bot_d_p, bot_d_s = pair_str(bot_d)
    mat_thick_p, mat_thick_s = pair_str(mat_thick)
    bot_thick_p, bot_thick_s = pair_str(bot_thick)
    dado_d_p, dado_d_s = pair_str(dado_d)

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
| **Side Panels** | {d_dr_p} &times; {h_dr_p} | {d_dr_s} &times; {h_dr_s} | 2 | Left and right outer drawer walls ({mat_thick_p} thick). |
| **Front & Back Panels** | {fb_cut_p} &times; {h_dr_p} | {fb_cut_s} &times; {h_dr_s} | 2 | Cut width for {joint_type} ({mat_thick_p} thick). |
| **Drawer Bottom Panel** | {bot_w_p} &times; {bot_d_p} | {bot_w_s} &times; {bot_d_s} | 1 | Cut size for {bot_thick_p} panel housed in {dado_d_p} dado grooves on 4 sides. |
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
    st.button("➕ New Project", key="btn_new_project_main", on_click=reset_to_new_project if not is_dirty else None)
    if is_dirty and st.session_state.get("btn_new_project_main"):
        st.session_state["pending_action"] = "new_project"
        st.rerun()

    # Form to save current setup
    with st.form("save_setup_form", clear_on_submit=False):
        st.write("Save Current Layout")
        st.text_input("Configuration Name", value=proj_name, key="setup_name_input", placeholder="e.g., Kitchen Base Drawer 1")
        st.form_submit_button("Save Configuration", on_click=handle_save_setup_callback, type="primary")

    if st.session_state.get("save_success_msg"):
        st.success(st.session_state["save_success_msg"])
        st.session_state["save_success_msg"] = None

    if st.session_state.get("save_error_msg"):
        st.error(st.session_state["save_error_msg"])
        st.session_state["save_error_msg"] = None

    # List and Load saved configurations
    st.write("Saved Projects")
    saved_setups = list_setups()
    
    if not saved_setups:
        st.info("No configurations saved yet.")
    else:
        for item in saved_setups:
            saved_slide_name = item.get('slide_name', 'Blum Tandem (5/8" Wood)')
            saved_mat = float(item.get('material_thickness', 0.625))
            saved_joint = item.get('joint_type', 'Butt Joint (Dominos / Dowels)')
            saved_bot = float(item.get('bottom_thickness', 0.25))
            saved_dado = float(item.get('dado_depth', 0.375))
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #2d2d30; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; background-color: #121214;">
                    <div style="font-weight: 600; color: #f8fafc; font-size: 0.95rem;">{item['name']}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.15rem;">
                        Mode: {'Box' if item['mode'] == 'drawer_box_mode' else 'Carcass'} | 
                        Slide: {int(item['slide_length'])}\" | 
                        Profile: {saved_slide_name}<br>
                        Wood: {float_to_fraction(saved_mat)} | Joint: {saved_joint}<br>
                        Bottom: {float_to_fraction(saved_bot)} ({float_to_fraction(saved_dado)} dado)<br>
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
