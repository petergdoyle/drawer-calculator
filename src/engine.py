import math
from fractions import Fraction
from typing import Dict, Any, Tuple, List

# Default Blum Slide Config
DEFAULT_SLIDE_CFG = {
    "name": 'Blum Tandem (5/8" Wood)',
    "width_tolerance": 0.375,
    "height_tolerance": 1.0,
    "min_depth_offset": 0.125,
    "bottom_recess": 0.5,
    "extension_below": 0.21875,
    "min_cab_width": 6.0,
    "min_cab_height": 3.5
}

MATERIAL_THICKNESS = 0.625  # 5/8" standard drawer wood thickness
REVEAL = 0.09375            # 3/32" inset front reveal all around
STANDARD_SLIDES = [9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0]

def float_to_fraction(val: float, max_denominator: int = 16) -> str:
    """Convert float value to string fractional representation (e.g. 15 3/8")."""
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
        "inset_width": inset_w,
        "inset_height": inset_h,
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
    cabinet_d = slide_len + slide_cfg["min_depth_offset"]

    inside_w = drawer_w - (2 * MATERIAL_THICKNESS)
    inside_d = slide_len - (2 * MATERIAL_THICKNESS)

    inset_w = cabinet_w - (2 * REVEAL)
    inset_h = cabinet_h - (2 * REVEAL)

    return {
        "mode": "carcass_mode",
        "cabinet_width": cabinet_w,
        "cabinet_height": cabinet_h,
        "cabinet_min_depth": cabinet_d,
        "drawer_width": drawer_w,
        "drawer_height": drawer_h,
        "drawer_depth": slide_len,
        "inside_width": inside_w,
        "inside_depth": inside_d,
        "inset_width": inset_w,
        "inset_height": inset_h,
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

