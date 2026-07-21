import streamlit as st
import pandas as pd
from src.storage import list_joint_bits
from src.engine import optimize_joint_layout, generate_joint_plot, float_to_fraction

st.markdown("""
<style>
    .joint-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #34d399, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .joint-subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    .result-card {
        background-color: #1a1a24;
        border: 1px solid #2d2d3d;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        margin-bottom: 1.5rem;
    }
    
    .exclusion-warning {
        background-color: #2e181b;
        border-left: 5px solid #ef4444;
        border-radius: 8px;
        padding: 1rem;
        color: #fca5a5;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="joint-title">📐 Joint Spacing Layout</div>', unsafe_allow_html=True)
st.markdown('<div class="joint-subtitle">Compute symmetrical tail and pin heights for drawer boxes and check Blum undermount dado clearance.</div>', unsafe_allow_html=True)

# Query joint bits from the database
db_bits = list_joint_bits()

# Fallback in case DB is not yet populated
if not db_bits:
    db_bits = [
        {"name": "50-8", "bit_type": "dovetail", "diameter": 0.250, "angle": 8.0, "pitch": 0.750},
        {"name": "60-8", "bit_type": "dovetail", "diameter": 0.3125, "angle": 8.0, "pitch": 0.750},
        {"name": "70-8", "bit_type": "dovetail", "diameter": 0.375, "angle": 8.0, "pitch": 0.750},
        {"name": "75-8", "bit_type": "dovetail", "diameter": 0.500, "angle": 8.0, "pitch": 0.750},
        {"name": "112-500", "bit_type": "dovetail", "diameter": 0.500, "angle": 12.0, "pitch": 0.750},
        {"name": "128-500", "bit_type": "dovetail", "diameter": 0.500, "angle": 18.0, "pitch": 0.750},
        {"name": "140-8", "bit_type": "dovetail", "diameter": 0.3125, "angle": 8.0, "pitch": 0.750},
        {"name": "163", "bit_type": "box_joint", "diameter": 0.09375, "angle": 0.0, "pitch": 0.1875},
        {"name": "166", "bit_type": "box_joint", "diameter": 0.1875, "angle": 0.0, "pitch": 0.375}
    ]

# Layout splits
col1, col2 = st.columns([4, 6])

with col1:
    st.subheader("⚙️ Spacing Config")
    
    # 1. Joinery Mode Selector
    joinery_mode = st.selectbox(
        "Joinery Mode",
        options=["Dovetail", "Box Joint"],
        key="joinery_mode"
    )
    
    # Filter bits based on Joinery Mode
    target_type = "dovetail" if joinery_mode == "Dovetail" else "box_joint"
    filtered_bits = [b for b in db_bits if b["bit_type"] == target_type]
    bit_names = [b["name"] for b in filtered_bits]
    
    # 2. Selectable Bit Dropdown
    def bit_display_format(name):
        b = next((x for x in filtered_bits if x["name"] == name), None)
        if not b:
            return name
        dia_frac = float_to_fraction(b["diameter"]).replace('"', '')
        if b["bit_type"] == "dovetail":
            return f"{name} ({dia_frac}\" @ {b['angle']:.0f}° Dovetail)"
        else:
            return f"{name} ({dia_frac}\" Box Joint)"

    selected_bit_name = st.selectbox(
        "Leigh RTJ400 Bit Profile",
        options=bit_names,
        format_func=bit_display_format,
        key="selected_bit_name"
    )
    
    selected_bit_cfg = next((b for b in filtered_bits if b["name"] == selected_bit_name), None)
    
    # 3. Pitch Selector (Dovetail Only)
    pitch_type = "Half Pitch (0.75\")"
    if joinery_mode == "Dovetail":
        pitch_type = st.selectbox(
            "Jig Spacing Pitch",
            options=["Half Pitch (0.75\")", "Full Pitch (1.5\")"],
            key="dovetail_pitch"
        )
        
    # 4. Calculation Mode
    calc_mode = st.selectbox(
        "Input Parameter Mode",
        options=["Target Box Height", "Drawer Front Height"],
        key="joint_calc_mode"
    )
    
    # 5. Inputs
    if calc_mode == "Target Box Height":
        target_val = st.number_input(
            "Target Drawer Box Height (in)",
            min_value=3.0,
            max_value=24.0,
            value=6.0,
            step=0.125
        )
    else:
        target_val = st.number_input(
            "Drawer Front Height (in)",
            min_value=4.0,
            max_value=24.0,
            value=8.0,
            step=0.125
        )
        st.caption("Valid box heights will be constrained to 0.5\" to 1.0\" below the front height.")

    st.markdown("---")
    st.info("💡 **Leigh RTJ400 Guide**:\n"
            "This utility matches your board dimensions to perfect symmetric jig settings while ensuring the Blum slide bottom dado doesn't cut through the joint interfaces.")

with col2:
    st.subheader("📊 Output Options")
    
    if selected_bit_cfg:
        # Run optimization
        results = optimize_joint_layout(
            joinery_type=joinery_mode,
            bit_cfg=selected_bit_cfg,
            mode=calc_mode,
            target_val=target_val,
            pitch_type=pitch_type
        )
        
        if not results:
            st.markdown(f"""
            <div class="exclusion-warning">
                <strong>🚫 No Valid Spacing Layouts Found</strong><br>
                All candidate drawer heights within the search range resulted in joint sockets (cutouts) intersecting the Blum dado exclusion zone (0.500" to 0.750" from the bottom).
                <br><br>
                <strong>To resolve this:</strong>
                <ul>
                    <li>Adjust your Target Drawer Box Height slightly up or down.</li>
                    <li>Try a different bit size or spacing pitch.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Let user select from top valid heights
            candidates = [f"{r['height']:.4f}\" ({float_to_fraction(r['height'])}) — Dev: {r['deviation']:.3f}\"" for r in results]
            
            selected_idx = st.selectbox(
                "Select Matching Symmetrical Height",
                options=range(len(results)),
                format_func=lambda idx: candidates[idx]
            )
            
            chosen_res = results[selected_idx]
            
            # Show summary
            st.markdown(f"""
            <div class="result-card">
                <h4 style="margin-top:0px; color:#34d399;">📐 Symmetrical Layout Detail</h4>
                <table style="width:100%; border-collapse:collapse; color:#cbd5e1; font-size:0.95rem;">
                    <tr style="border-bottom: 1px solid #2d2d3d;">
                        <td style="padding:0.5rem 0; font-weight:600;">Calculated Side Height:</td>
                        <td style="padding:0.5rem 0; text-align:right; font-weight:bold; color:#f8fafc;">{chosen_res['height']:.4f}" ({float_to_fraction(chosen_res['height'])})</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #2d2d3d;">
                        <td style="padding:0.5rem 0; font-weight:600;">{'Fingers Count' if joinery_mode == 'Box Joint' else 'Tails Count'}:</td>
                        <td style="padding:0.5rem 0; text-align:right; font-weight:bold; color:#f8fafc;">{chosen_res['num_elements']}</td>
                    </tr>
                    {f'''<tr style="border-bottom: 1px solid #2d2d3d;">
                        <td style="padding:0.5rem 0; font-weight:600;">Top/Bottom Half-Pins:</td>
                        <td style="padding:0.5rem 0; text-align:right; font-weight:bold; color:#f8fafc;">{chosen_res['half_pin_size']:.4f}" ({float_to_fraction(chosen_res['half_pin_size'])})</td>
                    </tr>''' if joinery_mode == 'Dovetail' else ''}
                    <tr>
                        <td style="padding:0.5rem 0; font-weight:600;">Dado Exclusion Check:</td>
                        <td style="padding:0.5rem 0; text-align:right; font-weight:bold; color:#34d399;">✅ PASSED (No overlaps)</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            # Render layout plot
            fig = generate_joint_plot(
                height=chosen_res["height"],
                joinery_type=joinery_mode,
                layout=chosen_res["layout"],
                bit_name=selected_bit_cfg["name"]
            )
            st.pyplot(fig)
            
            # List exact template markers coordinates table
            with st.expander("📝 Show Spacing Layout Coordinates (Y-Axis Templates)", expanded=False):
                st.write("Measurements from the bottom edge of the side panel up:")
                coord_data = []
                for idx, item in enumerate(chosen_res["layout"]):
                    coord_data.append({
                        "Element #": idx + 1,
                        "Type": item["type"].upper(),
                        "Start (in)": f"{item['start']:.4f}\"",
                        "Start (frac)": float_to_fraction(item['start']),
                        "End (in)": f"{item['end']:.4f}\"",
                        "End (frac)": float_to_fraction(item['end']),
                        "Thickness (in)": f"{item['end'] - item['start']:.4f}\""
                    })
                df_coords = pd.DataFrame(coord_data)
                st.dataframe(df_coords, hide_index=True)
