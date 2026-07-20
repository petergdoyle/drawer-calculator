import math
from fractions import Fraction
from typing import Dict, Any, Tuple, List

# Standard Hardware Constants
MATERIAL_THICKNESS = 0.625  # 5/8" standard drawer wood thickness
WIDTH_TOLERANCE = 0.375     # 3/8" (0.1875" per side) for Blum Tandem
HEIGHT_TOLERANCE = 1.000    # 1.000" total height clearance
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

def calculate_drawer_box(cabinet_w: float, cabinet_h: float, slide_len: float) -> Dict[str, Any]:
    """
    Given Cabinet Opening size, calculate optimal Drawer Box dimensions.
    """
    drawer_w = cabinet_w - WIDTH_TOLERANCE
    drawer_h = cabinet_h - HEIGHT_TOLERANCE
    drawer_d = slide_len

    inside_w = drawer_w - (2 * MATERIAL_THICKNESS)
    # Drawer box bottom is recessed, but inner depth (length front-to-back) is:
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
        "material_thickness": MATERIAL_THICKNESS
    }

def calculate_cabinet_opening(drawer_w: float, drawer_h: float, slide_len: float) -> Dict[str, Any]:
    """
    Given target Drawer Box size, calculate required Cabinet Opening space.
    """
    cabinet_w = drawer_w + WIDTH_TOLERANCE
    cabinet_h = drawer_h + HEIGHT_TOLERANCE
    cabinet_d = slide_len + 0.125  # Blum Tandem recommends slide length + 1/8" min cabinet depth

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
        "material_thickness": MATERIAL_THICKNESS
    }

def validate_inputs(width: float, height: float, slide_len: float) -> List[str]:
    """
    Validate size inputs and return a list of warnings or errors.
    """
    warnings = []
    if width <= 0 or height <= 0:
        warnings.append("Dimensions must be greater than zero.")
        return warnings

    if width < 6.0:
        warnings.append(f"Cabinet opening width ({width}\") is narrow. Blum locking devices require a drawer width of at least 4.875\".")
    
    if height < 3.5:
        warnings.append(f"Cabinet opening height ({height}\") is very low. Blum undermount slides require at least 1.0\" height clearance.")
    
    if slide_len not in STANDARD_SLIDES:
        warnings.append(f"Slide length {slide_len}\" is non-standard. Standard Blum Tandem lengths are: {', '.join([str(int(s)) for s in STANDARD_SLIDES])}\".")

    return warnings

def generate_svg(data: Dict[str, Any]) -> str:
    """
    Generate an interactive 2D wireframe SVG representation of the drawer box inside the carcass.
    """
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

    # Drawer Box clearances: Blum Tandem requires 3/16" left/right and 1/2" bottom (for locking mechanism)
    # The height clearance is 1" total, so we assume 0.5" top and 0.5" bottom clearance
    dr_x = cab_x + (0.1875 * scale)
    dr_y = cab_y + (0.5 * scale)

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
