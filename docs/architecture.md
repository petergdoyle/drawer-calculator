# Architecture Specification: Drawer Calculator

This document details the software architecture, folder structure, database schema, and orchestration layout of the **drawer-calculator** homelab project.

## 1. Directory Structure

The project follows a standard self-hosted Python layout:

```text
drawer-calculator/
├── .git/
├── data/                    # Local storage (ignored in Git, mounted in Docker)
│   └── drawers.db           # Persistent SQLite database
├── docs/
│   ├── architecture.md      # Architecture design (this file)
│   └── requirements.md      # Functional specifications
├── src/
│   ├── __init__.py
│   ├── engine.py            # Mathematical tolerances, safety checks, SVG renderer
│   └── storage.py           # SQLite persistence layer
├── app.py                   # Main Streamlit application
├── Dockerfile               # Containerization definition
├── docker-compose.yml       # Orchestration file mapping volume mount
├── Makefile                 # Make shortcuts for environment & run tasks
└── requirements.txt         # Project package dependencies
```

---

## 2. Core Components

### 2.1 UI Layer (`app.py`)
*   **Technology**: Streamlit.
*   **Duties**:
    *   Initialize UI theme parameters via custom CSS injections (custom fonts, glowing panel boarders, spacing tweaks).
    *   Maintain application states (e.g., loaded configurations, computation modes).
    *   Render inputs in sidebars, and dynamically refresh outputs on keypresses.
    *   Embed SVG graphics securely within markdown/HTML wrappers.
    *   Provide setup-saving text fields and listing tables to load or purge calculations.

### 2.2 Calculation Engine (`src/engine.py`)
*   **Technology**: Pure Python.
*   **Duties**:
    *   Apply undermount slide tolerances depending on calculation direction:
        *   Cabinet Width $\rightarrow$ Drawer Outer Width.
        *   Cabinet Height $\rightarrow$ Drawer Outer Height.
        *   Target Drawer Size $\rightarrow$ Cabinet Space.
    *   Perform structural boundary checks (e.g., minimum height, logical slide lengths).
    *   Generate a vector-drawn SVG string using input parameters, outlining the frame, inner clearance limits, side panel overlap configurations, and inset fronts.

### 2.3 Storage Layer (`src/storage.py`)
*   **Technology**: SQLite.
*   **Duties**:
    *   Provide an autonomous SQLite initializer. If `/app/data` is mounted (or local `data/` exists), create `drawers.db` and set up the schema.
    *   Execute CRUD operations safely using SQLite context managers.

---

## 3. Orchestration & Portability

### 3.1 Containerization (`Dockerfile` & `docker-compose.yml`)
*   The application is containerized using `python:3.11-slim`.
*   A volume mount maps `/app/data` on the container to `./data` on the host to ensure persistence of the database across restarts and updates.
*   Runs on port `8501`.

### 3.2 Task Automation (`Makefile`)
*   Standard Makefile to automate local virtual environments setup, running Streamlit, and composing Docker setups.
