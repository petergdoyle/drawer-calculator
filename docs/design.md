# Drawer Sizing and Undermount Slide Calculation Design

This document details the calculations, hardware requirements, and woodworking specifications for designing and building drawer boxes using undermount drawer slides (such as Blum Tandem or compatible profiles). It supports both **Drawer Box Mode** (calculating drawer dimensions from carcass openings) and **Carcass Mode** (calculating carcass openings from target drawer sizes).

---

## 1. Undermount Slide Sizing Principles

Undermount slides (like Blum Tandem, Salice Futura, etc.) are concealed beneath the drawer bottom. This hardware design dictates strict, uniform dimensional requirements:

*   **Drawer Box Width**: The outer drawer width must be the **inside cabinet opening width minus 3/8" (10 mm)** (for 5/8" thick drawer material). The inside drawer width is the opening width minus 1-5/8" (42 mm).
*   **Drawer Side Length**: The drawer box outer depth must match the slide nominal length exactly (e.g. a 15" slide requires a 15" long side panel).
*   **Drawer Box Height**: To provide sufficient vertical clearance for the slide runners, locking mechanisms, and top clearance, the cabinet opening height must be at least **1" (25 mm) higher** than the drawer box height.
*   **Drawer Bottom Recess**: The bottom panel must be recessed exactly **1/2" (13 mm)** up from the bottom edge of all four drawer box walls. This creates a recess channel to house the slide mechanisms.
*   **Sides Extension Below**: The side walls of the drawer must extend down **7/32" (5.5 mm)** below the bottom panel to shield the runners from view.

---

## 2. Step-by-Step Design Example: 32" Dresser Opening

### Target Requirements
*   **Cabinet Opening Width**: 32" (with spacers to bring the interior flush with the face frame)
*   **Cabinet Opening Height**: 8-5/8" (8.625")
*   **Slide Nominal Length**: 15"
*   **Material Thickness**: 5/8" (0.625")
*   **Target Drawer Height**: 6-11/16" (6.6875")
*   **Inset Front Reveal**: 3/32" (0.09375") all around

### Optimal Calculated Drawer Box Dimensions
*   **Outside Width**: **31-5/8" (31.625")**
    *   *Formula: Cabinet Opening (32.0") - Slide Width Tolerance (0.375")*
*   **Outside Depth/Length**: **15"**
    *   *Matches 15" slide nominal length.*
*   **Outside Height**: **6-11/16" (6.6875")**
    *   *Leaves 1-15/16" of top clearance inside the 8-5/8" opening (exceeding the 1" minimum requirement).*
*   **Inset Drawer Front Dimensions**: **31-13/16" Wide x 8-11/16" High**
    *   *Formula Width: Cabinet Opening (32.0") - 2 × Reveal (3/32" = 3/16") = 31-13/16"*
    *   *Formula Height: Cabinet Opening (8-5/8") - 2 × Reveal (3/32" = 3/16") = 8-11/16"*

### Woodworking Cut List (For 1 Drawer Box)
Assuming traditional construction where front and back panels are sandwiched between the side panels:
*   **2 Side Panels**: 15" Long × 6-11/16" High
*   **2 Front/Back Panels**: 30-3/8" Long × 6-11/16" High
    *   *Formula: Outside Width (31-5/8") - 2 × Material Thickness (5/8" = 1-1/4")*
*   **1 Drawer Bottom (1/4" plywood)**: 30-7/8" Wide × 14-1/2" Deep
    *   *Assumes a standard 1/4" deep dado slot grooved into all four sides.*

---

## 3. Critical Milling, Prep & Installation Specifications

To ensure the drawer slides engage smoothly and lock securely:

1.  **Bottom Dado Grooves**: Cut bottom dado slots exactly **1/2" up** from the bottom edge of all drawer box panels. The maximum thickness of the drawer lip below the bottom panel must not exceed 1/2".
2.  **Back Panel Notches**: The bottom edge of the **back panel only** requires two notches cut out to clear the slide runners. Each notch must be exactly **1-3/8" wide by 1/2" high**, cut flush with the outer side edges of the drawer box.
3.  **Rear Hook Registration**: Drill a **6mm (1/4") hole** into the back panel of the drawer box just above each notch (positioned 9/32" up from the inside drawer bottom) to catch the slide's rear registration hooks.
4.  **Locking Devices**: Screw the locking devices underneath the front bottom corners of the drawer box. Drill 6mm pilot holes on the inside of the sub-front, positioned 11mm (7/16") up from the bottom edge of the side walls.
5.  **Inset Front Mounting Setback**: Mount your drawer runners exactly **15/16" setback** from the front face of the cabinet frame. This accounts for the 3/4" thickness of your inset drawer front plus a 3/16" setback for the runner hardware to close flush.

---

## 4. Spreadsheets & Bi-Directional Formulas

You can automate these computations in Google Sheets or Microsoft Excel. Set up the following layout:

### Cell Layout Table

| Row | Column A (Labels) | Column B (Inputs/Formulas) | Column C (Notes) |
| :--- | :--- | :--- | :--- |
| **1** | **Parameter / Input Variable** | **Value** | **Unit / Note** |
| **2** | What are you calculating? | *[Drop-down: "Carcass Size" or "Drawer Box Size"]* | Toggle calculation mode |
| **3** | Material Thickness | `0.625` | 5/8" wood thickness |
| **4** | Slide Length | `15` | Slide nominal depth |
| **5** | Target/Actual Opening Width | *[User Input]* | Carcass width |
| **6** | Target/Actual Opening Height | *[User Input]* | Carcass height |
| **7** | Target/Actual Drawer Box Width | *[User Input]* | Drawer width |
| **8** | Target/Actual Drawer Box Height | *[User Input]* | Drawer height |

### Dynamic Output Formulas

Paste these formulas in Column B to automate calculations based on your B2 mode selection:

*   **Final Width Output (Cell B10)**:
    `=IF(B2="Carcass Size", B7 + 0.375, IF(B2="Drawer Box Size", B5 - 0.375, "Select Mode"))`
*   **Final Height Output (Cell B11)**:
    `=IF(B2="Carcass Size", B8 + 1.0, IF(B2="Drawer Box Size", B6 - 1.0, "Select Mode"))`
*   **Drawer Sides Cut Length (x2) (Cell B12)**:
    `=B4`
*   **Drawer Front/Back Panel Internal Width (x2) (Cell B13)**:
    `=IF(B2="Carcass Size", B7 - (2*B3), IF(B2="Drawer Box Size", (B5 - 0.375) - (2*B3), "Select Mode"))`

---

## 5. Citations and Installation Reference

*   [Blum Undermount Slide Sizing & Installation Specs](https://www.woodworkerexpress.com/answers/5832250/How-to-measure-for-undermount-drawer-slides)
*   [Dovetail Drawer Sizing Dimensions](https://www.eaglewoodworking.com/dovetail-drawers/measuring-instructions)
*   [Undermount Bottom Recess & Back Notching Guides](https://www.youtube.com/watch?v=I1fNqCM5cEY)
*   [Inset Drawer Front Setbacks and Hardware Mounts](https://sawdustgirl.com/installing-drawers-with-blum-tandem-plus-blumotion-drawer-slides/)
