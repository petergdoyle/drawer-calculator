import streamlit as st
from typing import Optional
from src.engine import parse_dimension, float_to_fraction, format_dimension_pair, inches_to_mm

def render_dimension_input(
    label: str,
    key: str,
    default_val: float = 12.0,
    min_val: float = 0.125,
    max_val: float = 120.0,
    help_text: Optional[str] = None,
    sidebar: bool = True,
    unit_system: str = "Fractional Inches (\")"
) -> float:
    """
    Renders a text input widget in Streamlit that accepts fractional or metric values.
    Provides real-time validation and formatted fraction & metric feedback.
    Returns the parsed float value in INCHES (rounded to 1/32" precision).
    """
    text_key = f"{key}_text"
    is_metric = unit_system.startswith("Metric")
    prev_unit_key = f"{key}_unit_system"

    # Track unit system changes to update default text input representation
    unit_changed = False
    if prev_unit_key not in st.session_state or st.session_state[prev_unit_key] != unit_system:
        st.session_state[prev_unit_key] = unit_system
        unit_changed = True

    current_val_inch = float(st.session_state.get(key, default_val))

    if text_key not in st.session_state or unit_changed:
        if is_metric:
            st.session_state[text_key] = f"{inches_to_mm(current_val_inch):.1f}"
        else:
            st.session_state[text_key] = float_to_fraction(current_val_inch).replace('"', '')

    container = st.sidebar if sidebar else st

    input_help = help_text or (
        "Enter millimeters (e.g. 520, 520mm) or fraction (e.g. 20 1/2)" 
        if is_metric else 
        "Enter fraction (e.g. 19 5/8, 19-5/8, 19 21/32) or decimal"
    )
    input_placeholder = "e.g. 520 mm" if is_metric else "e.g. 19 5/8"

    user_text = container.text_input(
        label,
        key=text_key,
        help=input_help,
        placeholder=input_placeholder
    )

    parsed_val, err_msg = parse_dimension(user_text, unit_system=unit_system)

    if err_msg:
        container.caption(f"❌ {err_msg}")
        fallback = float(st.session_state.get(key, default_val))
        return fallback

    if parsed_val < min_val:
        p_min, s_min = format_dimension_pair(min_val, unit_system)
        container.caption(f"⚠️ Min limit: {p_min} {s_min}")
        parsed_val = min_val
    elif parsed_val > max_val:
        p_max, s_max = format_dimension_pair(max_val, unit_system)
        container.caption(f"⚠️ Max limit: {p_max} {s_max}")
        parsed_val = max_val
    else:
        primary_str, secondary_str = format_dimension_pair(parsed_val, unit_system)
        container.caption(f"✔ **{primary_str}** {secondary_str}")

    st.session_state[key] = parsed_val
    return parsed_val
