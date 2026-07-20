import streamlit as st

# Custom styling for a modern, high-end dashboard feel
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .intro-title {
        font-size: 2.75rem;
        font-weight: 800;
        background: linear-gradient(90deg, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .intro-subtitle {
        font-size: 1.25rem;
        color: #94a3b8;
        margin-bottom: 2rem;
        font-weight: 400;
        line-height: 1.5;
    }

    .card {
        background-color: #1a1a24;
        border: 1px solid #2d2d3d;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        margin-bottom: 1.5rem;
    }
    
    .card-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .card-content {
        font-size: 0.95rem;
        color: #cbd5e1;
        line-height: 1.6;
    }

    .tip-box {
        background-color: #1a221f;
        border-left: 5px solid #10b981;
        border-radius: 8px;
        padding: 1rem;
        color: #a7f3d0;
        margin-top: 1rem;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="intro-title">📐 Drawer Calculator Fabric</div>', unsafe_allow_html=True)
st.markdown('<div class="intro-subtitle">A professional woodworking tool for planning, detailing, and calculating drawer boxes and cabinet carcass dimensions.</div>', unsafe_allow_html=True)

# Main Grid Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">
            <span style="color: #60a5fa;">📐</span> Bi-Directional Calculator
        </div>
        <div class="card-content">
            Our calculation engine works in two modes to fit your workflow:
            <ul>
                <li><strong>Drawer Box Mode</strong>: Enter your physical cabinet carcass opening dimensions, and the tool will automatically output the optimal outer drawer box dimensions and cut list.</li>
                <li><strong>Carcass Mode</strong>: Define a target drawer box size, and the engine determines the minimum required cabinet opening and depth parameters.</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <div class="card-title">
            <span style="color: #34d399;">🔧</span> Custom Slide Configurations
        </div>
        <div class="card-content">
            Different slide manufacturers (Blum, Salice, Grass, KV) and material thicknesses (5/8" vs 1/2" wood) require specific offsets.
            This tool allows you to:
            <ul>
                <li>Create, update, and delete custom slide configurations in the database.</li>
                <li>Save width, height, and depth tolerances tailored to your hardware spec.</li>
                <li>Instantly apply these configurations to generate custom woodworking blueprints and wireframe dimensions.</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">
            <span style="color: #fbbf24;">🪵</span> Standard Undermount Fit Principles
        </div>
        <div class="card-content">
            Undermount drawer runners require precise box geometry:
            <ol>
                <li><strong>Side Clearances</strong>: Undermount slides are concealed under the drawer bottom, requiring a specific gap between the drawer outer wall and the cabinet cabinet opening.</li>
                <li><strong>Drawer Bottom Recess</strong>: The drawer bottom must be recessed (typically <strong>1/2"</strong>) from the bottom edge of the sides to allow clearance for the locking devices and metal runners.</li>
                <li><strong>Lip Extension</strong>: The drawer sides must extend downwards below the bottom (typically <strong>7/32"</strong>) to hide the runner mechanisms completely from view.</li>
            </ol>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="tip-box">
        <strong>💡 Pro Woodworking Tip</strong>:<br>
        Always test fit a sample drawer box on a single set of slides before batching out your material. Small variations in plywood thickness or slide mounting positioning can affect the reveal and glide smoothness.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 🚀 Ready to calculate?")
if st.button("Go to Drawer Calculator", type="primary"):
    st.switch_page("app_pages/calculator.py")
