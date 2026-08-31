import streamlit as st
import pandas as pd
from src.storage import list_slides, save_slide, delete_slide
from src.engine import float_to_fraction
from src.ui_helpers import render_dimension_input

st.markdown("""
<style>
    .slides-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .slides-subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    .slide-card {
        border: 1px solid #2d2d30;
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        background-color: #121214;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    
    .slide-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #f8fafc;
        border-bottom: 1px solid #2d2d30;
        padding-bottom: 0.5rem;
        margin-bottom: 0.75rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.75rem 1.5rem;
        font-size: 0.9rem;
        color: #cbd5e1;
    }
    
    .metric-item {
        display: flex;
        justify-content: space-between;
    }
    
    .metric-label {
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="slides-title">🔧 Slide Configurations</div>', unsafe_allow_html=True)
st.markdown('<div class="slides-subtitle">Manage slide profile tolerances, setbacks, and clearances.</div>', unsafe_allow_html=True)

col1, col2 = st.columns([6, 4])

with col1:
    st.subheader("📋 Active Profiles")
    active_slides = list_slides()
    
    if not active_slides:
        st.info("No slide profiles configured.")
    else:
        for slide in active_slides:
            # Prevent deletion of baseline system slide profiles
            is_system_slide = slide["name"] in ['Blum Tandem (5/8" Wood)', 'Blum Tandem (1/2" Wood)', 'Generic Undermount']
            
            with st.container():
                st.markdown(f"""
                <div class="slide-card">
                    <div class="slide-header">
                        <span>🛠️ {slide['name']}</span>
                        <span style="font-size: 0.75rem; color: #10b981; background-color: #162c24; padding: 0.15rem 0.5rem; border-radius: 9999px;">
                            {'System Default' if is_system_slide else 'User Custom'}
                        </span>
                    </div>
                    <div class="metric-grid">
                        <div class="metric-item">
                            <span class="metric-label">Width Tolerance (clearance):</span>
                            <strong>{float_to_fraction(slide['width_tolerance'])} ({slide['width_tolerance']:.3f}")</strong>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Height Tolerance (clearance):</span>
                            <strong>{float_to_fraction(slide['height_tolerance'])} ({slide['height_tolerance']:.3f}")</strong>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Min. Depth Offset:</span>
                            <strong>{float_to_fraction(slide['min_depth_offset'])} ({slide['min_depth_offset']:.3f}")</strong>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Drawer Bottom Recess:</span>
                            <strong>{float_to_fraction(slide['bottom_recess'])} ({slide['bottom_recess']:.3f}")</strong>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Sides Extension Below:</span>
                            <strong>{float_to_fraction(slide['extension_below'])} ({slide['extension_below']:.3f}")</strong>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Min. Carcass Width:</span>
                            <strong>{float_to_fraction(slide['min_cab_width'])} ({slide['min_cab_width']:.3f}")</strong>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Action buttons for custom user slides
                if not is_system_slide:
                    btn_c1, btn_c2 = st.columns([1, 4])
                    with btn_c1:
                        if st.button("Delete", key=f"del_slide_{slide['id']}", type="secondary"):
                            if delete_slide(slide['id']):
                                st.success(f"Deleted profile: {slide['name']}")
                                st.rerun()
                            else:
                                st.error("Failed to delete slide profile.")
                    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

with col2:
    st.subheader("➕ Create New Profile")
    
    with st.form("add_slide_form", clear_on_submit=True):
        name = st.text_input("Profile Name", placeholder="e.g. Salice Futura (5/8\" Wood)")
        
        c1, c2 = st.columns(2)
        with c1:
            w_tol = render_dimension_input("Width Tolerance", key="new_slide_w_tol", default_val=0.375, min_val=0.0, max_val=2.0, help_text="Total width clearance (standard 3/8\").", sidebar=False)
            h_tol = render_dimension_input("Height Tolerance", key="new_slide_h_tol", default_val=1.0, min_val=0.0, max_val=3.0, help_text="Total height clearance (standard 1\").", sidebar=False)
            depth_offset = render_dimension_input("Min Depth Offset", key="new_slide_depth_offset", default_val=0.125, min_val=0.0, max_val=1.0, help_text="Setback offset beyond runner nominal length (standard 1/8\").", sidebar=False)
        with c2:
            recess = render_dimension_input("Bottom Recess", key="new_slide_recess", default_val=0.5, min_val=0.0, max_val=1.5, help_text="Recess height of drawer bottom (standard 1/2\").", sidebar=False)
            ext_below = render_dimension_input("Extension Below", key="new_slide_ext_below", default_val=0.21875, min_val=0.0, max_val=1.0, help_text="Extension of drawer side walls below bottom (standard 7/32\").", sidebar=False)
            min_w = render_dimension_input("Min Opening Width", key="new_slide_min_w", default_val=6.0, min_val=1.0, max_val=24.0, help_text="Minimum cabinet opening width (standard 6.0\").", sidebar=False)
            
        min_h = render_dimension_input("Min Opening Height", key="new_slide_min_h", default_val=3.5, min_val=1.0, max_val=24.0, help_text="Minimum cabinet opening height (standard 3.5\").", sidebar=False)
        
        submit = st.form_submit_button("Add Profile", type="primary")
        
        if submit:
            if not name.strip():
                st.error("Please enter a slide profile name.")
            elif any(s["name"].lower() == name.strip().lower() for s in active_slides):
                st.error("A slide configuration with this name already exists.")
            else:
                saved = save_slide(
                    name=name.strip(),
                    width_tolerance=w_tol,
                    height_tolerance=h_tol,
                    min_depth_offset=depth_offset,
                    bottom_recess=recess,
                    extension_below=ext_below,
                    min_cab_width=min_w,
                    min_cab_height=min_h
                )
                if saved:
                    st.success(f"Added slide profile '{name.strip()}' successfully!")
                    st.rerun()
                else:
                    st.error("Database error. Failed to save slide profile.")
