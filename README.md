# pRRTC & cuRobo Integration

This repository contains the research code for Asynchronous Dual-Arm Planning using pRRTC and NVIDIA cuRobo.

## Directory Structure

*   **`pRRTC_core/`**: The original GPU-Parallel RRT-Connect planner (Geometric).
    *   Contains the C++/CUDA implementation of pRRTC.
    *   Targeted for `pRRTC` paper reproduction.

*   **`curobo_integration/`**: The new research workspace for dynamic, kinodynamic, and trajectory optimization planning.
    *   Integration with NVIDIA Isaac Sim.
    *   Python-based "Manager" for dual-arm coordination.
    *   Space-Time RRT experiments.

## Getting Started

To run the original pRRTC:
```bash
cd pRRTC_core
cmake -B build
cmake --build build
```

To run the new cuRobo experiments:
```bash
cd curobo_integration
# Instructions coming soon
```
