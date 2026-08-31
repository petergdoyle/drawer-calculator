import math
import re
import csv
import io
from datetime import datetime
from fractions import Fraction
from typing import Dict, Any, Tuple, List, Optional, Union

# Default Blum Slide Config
# Default Blum Slide Config
DEFAULT_SLIDE_CFG = {
    "name": 'Blum Tandem (5/8" Wood)',
    "width_tolerance": 0.375,
    "height_tolerance": 1.0,
    "min_depth_offset": 0.65625,  # 21/32" standard Blum overlay depth clearance
    "bottom_recess": 0.5,
    "extension_below": 0.21875,
    "min_cab_width": 6.0,
    "min_cab_height": 3.5
}

MATERIAL_THICKNESS = 0.625  # 5/8" standard drawer wood thickness
REVEAL = 0.09375            # 3/32" inset front reveal all around
DADO_DEPTH = 0.25           # 1/4" bottom groove insertion depth on 4 sides
INSET_FRONT_SETBACK = 0.75  # 3/4" false front setback for inset drawers
STANDARD_SLIDES = [9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0]

def float_to_fraction(val: float, max_denominator: int = 32) -> str:
    """Convert float value to string fractional representation (e.g. 15 3/8", 15 21/32")."""
    if val is None or val <= 0:
        return '0"'
    whole = int(val)
    frac = val - whole
    numerator = round(frac * max_denominator)
    if numerator == 0:
        return f'{whole}"'
    elif numerator == max_denominator:
        return f'{whole + 1}"'
    else:
        f = Fraction(numerator, max_denominator)
        if whole > 0:
            return f'{whole} {f.numerator}/{f.denominator}"'
        else:
            return f'{f.numerator}/{f.denominator}"'

def round_to_32nd(val: float) -> float:
    """Round float value to nearest 1/32nd of an inch (0.03125")."""
    if val is None:
        return 0.0
    return round(val * 32.0) / 32.0

def parse_dimension(val: Any) -> Tuple[Optional[float], Optional[str]]:
    """
    Parse a dimension input (string, int, or float) into a float rounded to 1/32" precision.
    Returns a tuple of (parsed_float_value, error_message).
    Supports formats like:
      - 19.625, 19.625", 19
      - 19 5/8, 19 5/8", 19-5/8, 19-5/8"
      - 19 21/32, 21/32, 5/8"
    """
    if val is None:
        return None, "Empty input."

    if isinstance(val, (int, float)):
        if math.isnan(val) or math.isinf(val):
            return None, "Invalid numerical value."
        return round_to_32nd(float(val)), None

    s = str(val).strip()
    if not s:
        return None, "Empty input."

    # Strip common units and quotes
    s = re.sub(r'(?i)(inches|inch|in|["\'])', '', s).strip()

    # Try plain float/int first
    try:
        f = float(s)
        return round_to_32nd(f), None
    except ValueError:
        pass

    # Regex for mixed fraction e.g. "19 5/8" or "19-5/8" or "19  5/8"
    mixed_match = re.match(r'^(\d+)\s*[\s\-]\s*(\d+)\s*/\s*(\d+)$', s)
    if mixed_match:
        whole = int(mixed_match.group(1))
        num = int(mixed_match.group(2))
        denom = int(mixed_match.group(3))
        if denom == 0:
            return None, "Denominator cannot be zero."
        res = whole + (num / denom)
        return round_to_32nd(res), None

    # Regex for pure fraction e.g. "5/8" or "21/32"
    frac_match = re.match(r'^(\d+)\s*/\s*(\d+)$', s)
    if frac_match:
        num = int(frac_match.group(1))
        denom = int(frac_match.group(2))
        if denom == 0:
            return None, "Denominator cannot be zero."
        res = num / denom
        return round_to_32nd(res), None

    return None, f"Could not parse '{val}'. Try '19 5/8', '19.625', or '21/32'."


def calculate_drawer_box(cabinet_w: float, cabinet_h: float, slide_len: float, slide_cfg: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Given Cabinet Opening size and slide configuration, calculate optimal Drawer Box dimensions.
    """
    if slide_cfg is None:
        slide_cfg = DEFAULT_SLIDE_CFG

    drawer_w = cabinet_w - slide_cfg["width_tolerance"]
    drawer_h = cabinet_h - slide_cfg["height_tolerance"]
    drawer_d = slide_len

    inside_w = drawer_w - (2 * MATERIAL_THICKNESS)
    inside_d = drawer_d - (2 * MATERIAL_THICKNESS)

    bottom_w = inside_w + (2 * DADO_DEPTH)
    bottom_d = inside_d + (2 * DADO_DEPTH)

    min_depth_offset = slide_cfg.get("min_depth_offset", 0.65625)
    min_depth_overlay = drawer_d + min_depth_offset
    min_depth_inset = min_depth_overlay + INSET_FRONT_SETBACK

    # Inset front details (reveal is applied all around the cabinet opening)
    inset_w = cabinet_w - (2 * REVEAL)
    inset_h = cabinet_h - (2 * REVEAL)

    return {
        "mode": "drawer_box_mode",
        "cabinet_width": cabinet_w,
        "cabinet_height": cabinet_h,
        "drawer_width": drawer_w,
        "drawer_height": drawer_h,
        "drawer_depth": drawer_d,
        "inside_width": inside_w,
        "inside_depth": inside_d,
        "bottom_width": bottom_w,
        "bottom_depth": bottom_d,
        "dado_depth": DADO_DEPTH,
        "inset_width": inset_w,
        "inset_height": inset_h,
        "min_depth_overlay": min_depth_overlay,
        "min_depth_inset": min_depth_inset,
        "material_thickness": MATERIAL_THICKNESS,
        "slide_name": slide_cfg["name"]
    }

def calculate_cabinet_opening(drawer_w: float, drawer_h: float, slide_len: float, slide_cfg: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Given target Drawer Box size and slide configuration, calculate required Cabinet Opening space.
    """
    if slide_cfg is None:
        slide_cfg = DEFAULT_SLIDE_CFG

    cabinet_w = drawer_w + slide_cfg["width_tolerance"]
    cabinet_h = drawer_h + slide_cfg["height_tolerance"]
    min_depth_offset = slide_cfg.get("min_depth_offset", 0.65625)
    min_depth_overlay = slide_len + min_depth_offset
    min_depth_inset = min_depth_overlay + INSET_FRONT_SETBACK

    inside_w = drawer_w - (2 * MATERIAL_THICKNESS)
    inside_d = slide_len - (2 * MATERIAL_THICKNESS)

    bottom_w = inside_w + (2 * DADO_DEPTH)
    bottom_d = inside_d + (2 * DADO_DEPTH)

    inset_w = cabinet_w - (2 * REVEAL)
    inset_h = cabinet_h - (2 * REVEAL)

    return {
        "mode": "carcass_mode",
        "cabinet_width": cabinet_w,
        "cabinet_height": cabinet_h,
        "cabinet_min_depth": min_depth_overlay,
        "drawer_width": drawer_w,
        "drawer_height": drawer_h,
        "drawer_depth": slide_len,
        "inside_width": inside_w,
        "inside_depth": inside_d,
        "bottom_width": bottom_w,
        "bottom_depth": bottom_d,
        "dado_depth": DADO_DEPTH,
        "inset_width": inset_w,
        "inset_height": inset_h,
        "min_depth_overlay": min_depth_overlay,
        "min_depth_inset": min_depth_inset,
        "material_thickness": MATERIAL_THICKNESS,
        "slide_name": slide_cfg["name"]
    }

def validate_inputs(width: float, height: float, slide_len: float, slide_cfg: Dict[str, Any] = None) -> List[str]:
    """
    Validate size inputs against slide specifications and return a list of warnings.
    """
    if slide_cfg is None:
        slide_cfg = DEFAULT_SLIDE_CFG

    warnings = []
    if width <= 0 or height <= 0:
        warnings.append("Dimensions must be greater than zero.")
        return warnings

    min_drawer_w = slide_cfg["min_cab_width"] - slide_cfg["width_tolerance"]
    if width < slide_cfg["min_cab_width"]:
        warnings.append(f"Cabinet opening width ({width}\") is narrow. {slide_cfg['name']} locking devices require a drawer width of at least {min_drawer_w:.3f}\".")
    
    if height < slide_cfg["min_cab_height"]:
        warnings.append(f"Cabinet opening height ({height}\") is very low. {slide_cfg['name']} undermount slides require at least {slide_cfg['height_tolerance']:.3f}\" height clearance.")
    
    if slide_len not in STANDARD_SLIDES:
        warnings.append(f"Slide length {slide_len}\" is non-standard. Standard lengths are: {', '.join([str(int(s)) for s in STANDARD_SLIDES])}\".")

    return warnings

def generate_svg(data: Dict[str, Any], slide_cfg: Dict[str, Any] = None) -> str:
    """
    Generate an interactive 2D wireframe SVG representation of the drawer box inside the carcass.
    """
    if slide_cfg is None:
        slide_cfg = DEFAULT_SLIDE_CFG

    cab_w = data["cabinet_width"]
    cab_h = data["cabinet_height"]
    dr_w = data["drawer_width"]
    dr_h = data["drawer_height"]
    thick = data["material_thickness"]
    ins_w = data["inset_width"]
    ins_h = data["inset_height"]

    # Viewbox setup
    vb_w = 800
    vb_h = 500
    padding = 75

    # Scale to fit box
    scale_x = (vb_w - 2 * padding) / cab_w
    scale_y = (vb_h - 2 * padding) / cab_h
    scale = min(scale_x, scale_y)

    # Actual scaled sizes
    draw_cab_w = cab_w * scale
    draw_cab_h = cab_h * scale
    draw_dr_w = dr_w * scale
    draw_dr_h = dr_h * scale
    draw_thick = thick * scale
    draw_ins_w = ins_w * scale
    draw_ins_h = ins_h * scale

    # Position coordinates centered in SVG
    cab_x = (vb_w - draw_cab_w) / 2
    cab_y = (vb_h - draw_cab_h) / 2

    # Drawer Box clearances: slide width tolerance divided equally, height tolerance divided equally
    dr_x = cab_x + ((slide_cfg["width_tolerance"] / 2.0) * scale)
    dr_y = cab_y + ((slide_cfg["height_tolerance"] / 2.0) * scale)

    # Inset front offset (3/32" reveal all around)
    ins_x = cab_x + (REVEAL * scale)
    ins_y = cab_y + (REVEAL * scale)

    # Helper strings for labels
    cab_w_str = float_to_fraction(cab_w)
    cab_h_str = float_to_fraction(cab_h)
    dr_w_str = float_to_fraction(dr_w)
    dr_h_str = float_to_fraction(dr_h)
    ins_w_str = float_to_fraction(ins_w)
    ins_h_str = float_to_fraction(ins_h)

    # SVG definition
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb_w} {vb_h}" width="100%" height="100%" style="background-color: #121214; border-radius: 12px; font-family: 'Inter', system-ui, -apple-system, sans-serif;">
        <!-- Definitions for styles and marker arrows -->
        <defs>
            <style>
                .cabinet-line {{ stroke: #3b82f6; stroke-width: 2; stroke-dasharray: 6,4; fill: none; }}
                .drawer-outer {{ stroke: #f59e0b; stroke-width: 2.5; fill: #1e1b15; fill-opacity: 0.4; }}
                .drawer-inner {{ stroke: #f59e0b; stroke-width: 1.5; stroke-opacity: 0.7; fill: none; }}
                .inset-front {{ stroke: #10b981; stroke-width: 1.5; stroke-dasharray: 4,4; fill: #10b981; fill-opacity: 0.05; }}
                .dim-line {{ stroke: #6b7280; stroke-width: 1; }}
                .dim-arrow {{ fill: #6b7280; }}
                .text-cab {{ fill: #60a5fa; font-size: 14px; font-weight: 600; text-anchor: middle; }}
                .text-dr {{ fill: #fbbf24; font-size: 14px; font-weight: 600; text-anchor: middle; }}
                .text-ins {{ fill: #34d399; font-size: 13px; font-weight: 500; text-anchor: middle; }}
                .text-thick {{ fill: #f59e0b; font-size: 10px; text-anchor: middle; }}
            </style>
            
            <marker id="arrow-start" viewBox="0 0 10 10" refX="0" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 10 0 L 0 5 L 10 10 z" class="dim-arrow"/>
            </marker>
            <marker id="arrow-end" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" class="dim-arrow"/>
            </marker>
        </defs>
 
        <!-- Dynamic Grid Pattern -->
        <g stroke="#1f1f23" stroke-width="1">
            <path d="M 0,50 L {vb_w},50 M 0,100 L {vb_w},100 M 0,150 L {vb_w},150 M 0,200 L {vb_w},200 M 0,250 L {vb_w},250 M 0,300 L {vb_w},300 M 0,350 L {vb_w},350 M 0,400 L {vb_w},400 M 0,450 L {vb_w},450" />
            <path d="M 50,0 L 50,{vb_h} M 100,0 L 100,{vb_h} M 150,0 L 150,{vb_h} M 200,0 L 200,{vb_h} M 250,0 L 250,{vb_h} M 300,0 L 300,{vb_h} M 350,0 L 350,{vb_h} M 400,0 L 400,{vb_h} M 450,0 L 450,{vb_h} M 500,0 L 500,{vb_h} M 550,0 L 550,{vb_h} M 600,0 L 600,{vb_h} M 650,0 L 650,{vb_h} M 700,0 L 700,{vb_h} M 750,0 L 750,{vb_h}" />
        </g>
 
        <!-- 1. Cabinet Opening -->
        <rect x="{cab_x}" y="{cab_y}" width="{draw_cab_w}" height="{draw_cab_h}" class="cabinet-line" />
        
        <!-- 2. Inset Drawer Front (dashed reveal guide) -->
        <rect x="{ins_x}" y="{ins_y}" width="{draw_ins_w}" height="{draw_ins_h}" rx="3" class="inset-front" />
 
        <!-- 3. Drawer Box Outer Boundary -->
        <rect x="{dr_x}" y="{dr_y}" width="{draw_dr_w}" height="{draw_dr_h}" rx="2" class="drawer-outer" />
 
        <!-- 4. Drawer Box Interior (Bottom and Side wood thicknesses) -->
        <!-- Left Side Inner Wall -->
        <line x1="{dr_x + draw_thick}" y1="{dr_y}" x2="{dr_x + draw_thick}" y2="{dr_y + draw_dr_h - draw_thick}" class="drawer-inner" />
        <!-- Right Side Inner Wall -->
        <line x1="{dr_x + draw_dr_w - draw_thick}" y1="{dr_y}" x2="{dr_x + draw_dr_w - draw_thick}" y2="{dr_y + draw_dr_h - draw_thick}" class="drawer-inner" />
        <!-- Bottom Panel Inner Wall -->
        <line x1="{dr_x + draw_thick}" y1="{dr_y + draw_dr_h - draw_thick}" x2="{dr_x + draw_dr_w - draw_thick}" y2="{dr_y + draw_dr_h - draw_thick}" class="drawer-inner" />
 
        <!-- 5. Dimension Markers & Annotations -->
        <!-- Cabinet Width Dimension -->
        <line x1="{cab_x}" y1="{cab_y - 25}" x2="{cab_x + draw_cab_w}" y2="{cab_y - 25}" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" />
        <text x="{cab_x + draw_cab_w / 2}" y="{cab_y - 35}" class="text-cab">Cabinet Width: {cab_w_str} ({cab_w:.3f}")</text>
 
        <!-- Cabinet Height Dimension -->
        <line x1="{cab_x - 25}" y1="{cab_y}" x2="{cab_x - 25}" y2="{cab_y + draw_cab_h}" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" />
        <text x="{cab_x - 35}" y="{cab_y + draw_cab_h / 2}" class="text-cab" transform="rotate(-90, {cab_x - 35}, {cab_y + draw_cab_h / 2})">Cabinet Height: {cab_h_str} ({cab_h:.3f}")</text>
 
        <!-- Drawer Width Dimension -->
        <line x1="{dr_x}" y1="{dr_y + draw_dr_h / 2}" x2="{dr_x + draw_dr_w}" y2="{dr_y + draw_dr_h / 2}" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" />
        <text x="{dr_x + draw_dr_w / 2}" y="{dr_y + draw_dr_h / 2 - 8}" class="text-dr">Drawer Width: {dr_w_str} ({dr_w:.3f}")</text>
 
        <!-- Drawer Height Dimension -->
        <line x1="{dr_x + draw_dr_w / 2}" y1="{dr_y}" x2="{dr_x + draw_dr_w / 2}" y2="{dr_y + draw_dr_h}" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" />
        <text x="{dr_x + draw_dr_w / 2 - 8}" y="{dr_y + draw_dr_h / 2}" class="text-dr" transform="rotate(-90, {dr_x + draw_dr_w / 2 - 8}, {dr_y + draw_dr_h / 2})">Drawer Height: {dr_h_str} ({dr_h:.3f}")</text>
 
        <!-- Inset Front Label (Drawn in bottom right area) -->
        <text x="{cab_x + draw_cab_w - 90}" y="{cab_y + draw_cab_h - 20}" class="text-ins">Inset Front: {ins_w_str} x {ins_h_str}</text>
        
        <!-- Material Thickness label -->
        <text x="{dr_x + draw_thick / 2}" y="{dr_y + 15}" class="text-thick" transform="rotate(-90, {dr_x + draw_thick / 2}, {dr_y + 15})">5/8"</text>
    </svg>"""
    
    return svg


def optimize_joint_layout(
    joinery_type: str, 
    bit_cfg: Dict[str, Any], 
    mode: str, 
    target_val: float, 
    pitch_type: str = "Half Pitch (0.75\")"
) -> List[Dict[str, Any]]:
    """
    Search for valid drawer side heights and coordinate configurations that:
    1. Enforce perfect symmetry (odd fingers for Box Joint, equal half-pins for Dovetail).
    2. Check collisions with the Blum dado exclusion zone ([0.500", 0.750"]).
    3. Are within the search bounds.
    """
    results = []
    
    # Determine the search bounds for box height H
    if mode == "Target Box Height":
        min_h = max(2.0, target_val - 1.0)
        max_h = target_val + 1.0
    else:  # Drawer Front Height
        # valid box heights must be within 0.5" to 1.0" below the front height
        min_h = max(2.0, target_val - 1.0)
        max_h = target_val - 0.5

    dado_start = 0.500
    dado_end = 0.750
    
    if joinery_type.lower() == "box joint":
        # Box joint finger size is the cutter diameter
        F = bit_cfg["diameter"]
        # Find candidates by sweeping odd integers N
        # We want H = N * F
        min_n = int(min_h / F)
        max_n = int(max_h / F) + 1
        
        for N in range(min_n, max_n + 1):
            if N % 2 == 0:
                continue  # enforce odd finger counts for symmetry
            
            H = N * F
            if H < min_h or H > max_h:
                continue
                
            # Sockets are at odd indices i (starting with i=0 as finger, i=1 as socket)
            # Socket intervals: [i * F, (i + 1) * F] for odd i
            overlap = False
            layout = []
            
            for i in range(N):
                is_socket = (i % 2 == 1)
                start_y = i * F
                end_y = (i + 1) * F
                
                layout_item = {
                    "type": "socket" if is_socket else "finger",
                    "start": start_y,
                    "end": end_y
                }
                layout.append(layout_item)
                
                if is_socket:
                    # check overlap with dado
                    if max(start_y, dado_start) < min(end_y, dado_end):
                        overlap = True
            
            if not overlap:
                # Calculate deviation from target height
                if mode == "Target Box Height":
                    dev = abs(H - target_val)
                else:
                    dev = abs(H - (target_val - 0.75))
                
                results.append({
                    "height": H,
                    "num_elements": N,
                    "half_pin_size": 0.0,
                    "layout": layout,
                    "deviation": dev,
                    "joinery_type": "Box Joint"
                })
                
    else:  # Dovetail
        # Dovetail configuration
        D = bit_cfg["diameter"]
        # Determine pitch P based on selection
        P = 1.500 if "1.5" in pitch_type else 0.750
        
        # We sweep candidate heights H in steps of 1/32" (0.03125")
        sweep_resolution = 0.03125
        num_steps = int((max_h - min_h) / sweep_resolution) + 1
        
        for step in range(num_steps):
            H = min_h + step * sweep_resolution
            # Sweep tail counts N
            min_n = 1
            max_n = int(H / P) + 2
            
            for N in range(min_n, max_n + 1):
                # Calculate half-pin size: H_pin = (H - (N - 1)*P - D) / 2
                H_pin = (H - (N - 1) * P - D) / 2.0
                
                if H_pin < 0.1875 or H_pin > 0.500:
                    continue
                    
                # Sockets (pin locations) cut out of the side board
                overlap = False
                layout = []
                
                # Bottom half-pin socket
                layout.append({"type": "socket", "start": 0.0, "end": H_pin})
                
                # Tails and intermediate pins
                for i in range(N):
                    # Tail interval
                    tail_start = H_pin + i * P
                    tail_end = H_pin + D + i * P
                    layout.append({"type": "tail", "start": tail_start, "end": tail_end})
                    
                    # If not the last tail, add intermediate socket
                    if i < N - 1:
                        sock_start = tail_end
                        sock_end = H_pin + (i + 1) * P
                        layout.append({"type": "socket", "start": sock_start, "end": sock_end})
                        # check intermediate socket overlap with dado
                        if max(sock_start, dado_start) < min(sock_end, dado_end):
                            overlap = True
                
                # Top half-pin socket
                layout.append({"type": "socket", "start": H - H_pin, "end": H})
                
                # Bottom and top half-pin socket check
                if max(H - H_pin, dado_start) < min(H, dado_end):
                    overlap = True
                    
                if not overlap:
                    # Calculate deviation from target height
                    if mode == "Target Box Height":
                        dev = abs(H - target_val)
                    else:
                        dev = abs(H - (target_val - 0.75))
                    
                    results.append({
                        "height": H,
                        "num_elements": N,
                        "half_pin_size": H_pin,
                        "layout": sorted(layout, key=lambda x: x["start"]),
                        "deviation": dev,
                        "joinery_type": f"Dovetail ({pitch_type})"
                    })
                    break

    # Sort results by deviation (closest to target height first)
    results = sorted(results, key=lambda x: x["deviation"])
    return results


def generate_joint_plot(height: float, joinery_type: str, layout: List[Dict[str, Any]], bit_name: str):
    """Generate a Matplotlib figure plotting the joint spacing layout schematic."""
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    fig, ax = plt.subplots(figsize=(5.5, 7.5))
    board_w = 2.0
    
    # Plot background board
    ax.add_patch(patches.Rectangle(
        (0, 0), board_w, height, 
        facecolor="#18181b", edgecolor="#3f3f46", linewidth=2.5, 
        label="Drawer Side Panel"
    ))
    
    # Plot Blum dado exclusion band [0.500", 0.750"]
    ax.add_patch(patches.Rectangle(
        (0, 0.500), board_w, 0.250, 
        facecolor="#7f1d1d", alpha=0.45, hatch="//", 
        edgecolor="#ef4444", linewidth=1.5, linestyle="--", 
        label="Blum Runner Dado (1/4\" @ 1/2\" up)"
    ))
    
    # Draw sockets & wood fingers
    for item in layout:
        start_y = item["start"]
        end_y = item["end"]
        thick = end_y - start_y
        
        if item["type"] == "socket":
            # Left cutout
            ax.add_patch(patches.Rectangle(
                (0, start_y), 0.45, thick, 
                facecolor="#09090b", edgecolor="#7f1d1d", linewidth=1
            ))
            # Right cutout
            ax.add_patch(patches.Rectangle(
                (board_w - 0.45, start_y), 0.45, thick, 
                facecolor="#09090b", edgecolor="#7f1d1d", linewidth=1
            ))
        else:
            # Wood structure elements (fingers/tails)
            color_face = "#b45309" if "dovetail" in joinery_type.lower() else "#047857"
            color_edge = "#d97706" if "dovetail" in joinery_type.lower() else "#059669"
            label_text = "Dovetail Tail" if "dovetail" in joinery_type.lower() else "Finger Joint"
            
            ax.add_patch(patches.Rectangle(
                (0, start_y), 0.45, thick, 
                facecolor=color_face, edgecolor=color_edge, alpha=0.6, linewidth=1
            ))
            ax.add_patch(patches.Rectangle(
                (board_w - 0.45, start_y), 0.45, thick, 
                facecolor=color_face, edgecolor=color_edge, alpha=0.6, linewidth=1
            ))

    # Add Y-coordinate markers on ticks
    y_ticks = [0.0, height]
    for item in layout:
        y_ticks.extend([item["start"], item["end"]])
    
    # Deduplicate and sort ticks
    y_ticks = sorted(list(set(round(y, 5) for y in y_ticks)))
    
    # Prune overlaps to keep plot readable
    pruned_ticks = []
    pruned_labels = []
    for val in y_ticks:
        if not any(abs(val - pv) < 0.05 for pv in pruned_ticks):
            pruned_ticks.append(val)
            frac_str = float_to_fraction(val, 32).replace('"', '')
            pruned_labels.append(f"{val:.3f}\" ({frac_str}\")")
            ax.axhline(y=val, color="#27272a", linestyle=":", linewidth=0.8)
    
    ax.set_yticks(pruned_ticks)
    ax.set_yticklabels(pruned_labels, fontsize=8.5, color="#a1a1aa")
    
    ax.set_xticks([0.225, board_w / 2.0, board_w - 0.225])
    ax.set_xticklabels(["Joint End A", "Drawer Center", "Joint End B"], fontsize=9.5, color="#a1a1aa")
    
    ax.set_xlim(-0.25, board_w + 0.25)
    ax.set_ylim(-0.15, height + 0.15)
    ax.set_title(f"Joint Profile (Height: {height:.3f}\", Bit: {bit_name})", fontsize=11.5, color="#f4f4f5", pad=12, fontweight="bold")
    
    # Theme configuration
    ax.set_facecolor("#09090b")
    fig.patch.set_facecolor("#09090b")
    for spine in ax.spines.values():
        spine.set_color('#27272a')
        spine.set_linewidth(1.2)
    ax.tick_params(colors='#71717a')
    
    ax.legend(
        facecolor="#18181b", edgecolor="#27272a", labelcolor="#e4e4e7", 
        loc="lower center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=8.5
    )
    
    plt.tight_layout()
    return fig


def generate_csv_cutlist(results: Dict[str, Any], slide_cfg: Dict[str, Any] = None) -> str:
    """Generate a CSV string representation of the drawer cut list."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Component", "Qty", 
        "Width_Decimal", "Width_Fractional", 
        "Height_Decimal", "Height_Fractional", 
        "Depth_Decimal", "Depth_Fractional", 
        "Notes"
    ])

    w_cab = results["cabinet_width"]
    h_cab = results["cabinet_height"]
    w_dr = results["drawer_width"]
    h_dr = results["drawer_height"]
    d_dr = results["drawer_depth"]
    in_w = results["inside_width"]
    in_d = results["inside_depth"]
    bot_w = results.get("bottom_width", in_w + 0.5)
    bot_d = results.get("bottom_depth", in_d + 0.5)
    w_ins = results["inset_width"]
    h_ins = results["inset_height"]
    min_dep_overlay = results.get("min_depth_overlay", d_dr + 0.65625)
    min_dep_inset = results.get("min_depth_inset", min_dep_overlay + 0.75)

    writer.writerow(["Cabinet Opening", 1, f"{w_cab:.4f}", float_to_fraction(w_cab), f"{h_cab:.4f}", float_to_fraction(h_cab), f"{min_dep_overlay:.4f}", float_to_fraction(min_dep_overlay), f"Min overlay depth: {min_dep_overlay:.4f}\", Min inset depth: {min_dep_inset:.4f}\""])
    writer.writerow(["Drawer Box Outside", 1, f"{w_dr:.4f}", float_to_fraction(w_dr), f"{h_dr:.4f}", float_to_fraction(h_dr), f"{d_dr:.4f}", float_to_fraction(d_dr), "Total external drawer dimensions"])
    writer.writerow(["Side Panels", 2, "-", "-", f"{h_dr:.4f}", float_to_fraction(h_dr), f"{d_dr:.4f}", float_to_fraction(d_dr), "Left and right outer drawer walls (5/8\" thickness)"])
    writer.writerow(["Front & Back Panels", 2, f"{in_w:.4f}", float_to_fraction(in_w), f"{h_dr:.4f}", float_to_fraction(h_dr), "-", "-", "Fit between sides (Calculated width: Outside Width - 1.25\")"])
    writer.writerow(["Drawer Bottom Panel", 1, f"{bot_w:.4f}", float_to_fraction(bot_w), "-", "-", f"{bot_d:.4f}", float_to_fraction(bot_d), "Cut size including 1/4\" dado insertion on 4 sides"])
    writer.writerow(["Inside Workspace Clearance", 1, f"{in_w:.4f}", float_to_fraction(in_w), "-", "-", f"{in_d:.4f}", float_to_fraction(in_d), "Maximum flat interior workspace clearance"])
    writer.writerow(["Inset Front Reveal", 1, f"{w_ins:.4f}", float_to_fraction(w_ins), f"{h_ins:.4f}", float_to_fraction(h_ins), "-", "-", "Calculated with uniform 3/32\" reveal clearances"])

    return output.getvalue()


def generate_txt_summary(results: Dict[str, Any], slide_cfg: Dict[str, Any] = None) -> str:
    """Generate a clean text summary of the calculation results and cut list."""
    slide_name = slide_cfg["name"] if slide_cfg else results.get("slide_name", "Undermount Slide")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    w_cab = results["cabinet_width"]
    h_cab = results["cabinet_height"]
    w_dr = results["drawer_width"]
    h_dr = results["drawer_height"]
    d_dr = results["drawer_depth"]
    in_w = results["inside_width"]
    in_d = results["inside_depth"]
    bot_w = results.get("bottom_width", in_w + 0.5)
    bot_d = results.get("bottom_depth", in_d + 0.5)
    w_ins = results["inset_width"]
    h_ins = results["inset_height"]

    min_dep_overlay = results.get("min_depth_overlay", d_dr + 0.65625)
    min_dep_inset = results.get("min_depth_inset", min_dep_overlay + 0.75)
    recess = slide_cfg["bottom_recess"] if slide_cfg else 0.5
    ext_below = slide_cfg["extension_below"] if slide_cfg else 0.21875

    txt = f"""========================================================================
📐 DRAWER CALCULATOR - CUT LIST & WORKSTATION SUMMARY
Generated: {now_str}
Hardware Profile: {slide_name}
Calculation Mode: {results.get('mode', 'drawer_box_mode').replace('_', ' ').title()}
========================================================================

--- OVERALL SPECIFICATIONS ---
Cabinet Opening Width:      {w_cab:.4f}" ({float_to_fraction(w_cab)})
Cabinet Opening Height:     {h_cab:.4f}" ({float_to_fraction(h_cab)})
Min. Overlay Carcass Depth: {min_dep_overlay:.4f}" ({float_to_fraction(min_dep_overlay)})
Min. Inset Carcass Depth:   {min_dep_inset:.4f}" ({float_to_fraction(min_dep_inset)}) [Includes 3/4" Front Setback]

Drawer Box Outside Width:   {w_dr:.4f}" ({float_to_fraction(w_dr)})
Drawer Box Outside Height:  {h_dr:.4f}" ({float_to_fraction(h_dr)})
Drawer Box Outside Depth:   {d_dr:.4f}" ({float_to_fraction(d_dr)})

Inside Workspace Width:     {in_w:.4f}" ({float_to_fraction(in_w)})
Inside Workspace Depth:     {in_d:.4f}" ({float_to_fraction(in_d)})

Inset Front Dimensions:     {w_ins:.4f}" x {h_ins:.4f}" ({float_to_fraction(w_ins)} x {float_to_fraction(h_ins)})

--- CUT LIST BREAKDOWN ---
1. Side Panels (Qty: 2)
   - Height: {h_dr:.4f}" ({float_to_fraction(h_dr)})
   - Length: {d_dr:.4f}" ({float_to_fraction(d_dr)})
   - Material Thickness: 5/8" (0.625")

2. Front & Back Panels (Qty: 2)
   - Width:  {in_w:.4f}" ({float_to_fraction(in_w)})
   - Height: {h_dr:.4f}" ({float_to_fraction(h_dr)})
   - Material Thickness: 5/8" (0.625")

3. Drawer Bottom Panel Cut Size (Qty: 1) [Housed in 1/4" Dado Grooves]
   - Cut Width: {bot_w:.4f}" ({float_to_fraction(bot_w)})  [Inside Width + 1/2" Dado Insertion]
   - Cut Depth: {bot_d:.4f}" ({float_to_fraction(bot_d)})  [Inside Depth + 1/2" Dado Insertion]

4. Inside Workspace Clearance (Qty: 1)
   - Clear Width: {in_w:.4f}" ({float_to_fraction(in_w)})
   - Clear Depth: {in_d:.4f}" ({float_to_fraction(in_d)})

5. Inset Drawer Front (Qty: 1)
   - Width:  {w_ins:.4f}" ({float_to_fraction(w_ins)})
   - Height: {h_ins:.4f}" ({float_to_fraction(h_ins)})
   - Clearance Reveal: 3/32" (0.09375") all around

--- HARDWARE & INSTALLATION SPECS ---
- Bottom Recess Height:     {recess:.4f}" ({float_to_fraction(recess)})
- Side Extension Below:     {ext_below:.5f}" ({float_to_fraction(ext_below)})
- Rear Locking Dado Notch:  Standard 1/4" dado @ 1/2" up from bottom edge

========================================================================
"""
    return txt


