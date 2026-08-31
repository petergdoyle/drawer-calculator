import streamlit as st
from typing import Optional
from src.engine import parse_dimension, float_to_fraction

def render_dimension_input(
    label: str,
    key: str,
    default_val: float = 12.0,
    min_val: float = 0.125,
    max_val: float = 120.0,
    help_text: Optional[str] = None,
    sidebar: bool = True
) -> float:
    """
    Renders a text input widget in Streamlit that accepts fractional or decimal values.
    Provides real-time validation and formatted fraction & decimal feedback.
    Returns the parsed float value (rounded to 1/32" precision).
    """
    text_key = f"{key}_text"

    # Initialize text_key once if not present in session state
    if text_key not in st.session_state:
        if key in st.session_state and isinstance(st.session_state[key], (int, float)):
            st.session_state[text_key] = float_to_fraction(float(st.session_state[key])).replace('"', '')
        else:
            st.session_state[text_key] = float_to_fraction(default_val).replace('"', '')

    container = st.sidebar if sidebar else st

    user_text = container.text_input(
        label,
        key=text_key,
        help=help_text or "Enter decimal (e.g. 19.625) or fraction (e.g. 19 5/8, 19-5/8, 19 21/32)",
        placeholder="e.g. 19 5/8 or 19.625"
    )

    parsed_val, err_msg = parse_dimension(user_text)

    if err_msg:
        container.caption(f"❌ {err_msg}")
        fallback = float(st.session_state.get(key, default_val))
        return fallback

    if parsed_val < min_val:
        container.caption(f"⚠️ Min limit: {float_to_fraction(min_val)} ({min_val}\")")
        parsed_val = min_val
    elif parsed_val > max_val:
        container.caption(f"⚠️ Max limit: {float_to_fraction(max_val)} ({max_val}\")")
        parsed_val = max_val
    else:
        frac_str = float_to_fraction(parsed_val)
        container.caption(f"✔ **{frac_str}** ({parsed_val:.4f}\")")

    st.session_state[key] = parsed_val
    return parsed_val
