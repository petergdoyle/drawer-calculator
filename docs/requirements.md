# Requirements Specification: Drawer Calculator

This document details the functional and non-functional requirements for the **drawer-calculator** tool.

## 1. Functional Requirements

### 1.1 Bi-Directional Calculations
The application must perform calculations in two directions:
*   **Drawer Box Mode**: Given the dimensions of the cabinet opening/cavity, calculate the optimal dimensions of the drawer box.
*   **Carcass Mode**: Given the desired drawer box size, calculate the required cabinet cavity opening dimensions.

### 1.2 Hardware and Material Standards
*   **Material Thickness**: Default to 5/8" (0.625") drawer box side panel thickness.
*   **Slide Tolerances (Blum Tandem undermounts)**:
    *   **Width**: Outside Drawer Width = Cabinet Opening Width - 3/8" (0.375")
    *   **Height**: Outside Drawer Height = Cabinet Opening Height - 1" (1.000")
    *   **Depth**: Drawer Outside Depth (Side Panel Length) = Nominal Slide Length.
*   **Slide Nominal Lengths**: Must support standard slide sizes: 9", 12", 15", 18", 21", 24", 27", 30".
*   **Inset Drawer Front Helper**:
    *   For a given/computed cabinet opening, calculate the inset drawer front dimensions assuming a uniform **3/32" (0.09375") reveal** on all four sides.
    *   Width = Cabinet Opening Width - 3/16" (0.1875")
    *   Height = Cabinet Opening Height - 3/16" (0.1875")

### 1.3 UI & Visual Outputs
*   **Calculations Summary**: A clean markdown text breakdown displaying the calculated values in decimal and fractional notation (nearest 1/16" or 1/32").
*   **2D Wireframe Visualizer**: An interactive SVG showing:
    *   Cabinet cavity boundaries.
    *   Drawer box outer and inner margins (highlighting 5/8" material thickness).
    *   Inset front outline.
    *   Dimension arrows/callouts.
*   **Validation Warnings**: Display alerts if inputs represent physically impossible dimensions (e.g. width/height too small for slides, zero/negative values).

### 1.4 State Persistence
*   Save setup configurations under user-defined names.
*   Retrieve, delete, and view stored setups.
*   Persistent storage using an embedded SQLite database in `/app/data` (which translates to local project `/data` directory when running natively).

---

## 2. Non-Functional Requirements
*   **Homelab Compliance**: The application must run standalone, containerized via Docker Compose, storing state in an externalizable persistent volume (`/app/data`).
*   **Frameworks**: Streamlit (Python) for rapid responsive dashboard builds.
*   **Portability**: Supported on local python environment and Docker.
*   **Aesthetics**: Sleek dark mode styling with premium layout rendering, typography, and clean color schemes.
