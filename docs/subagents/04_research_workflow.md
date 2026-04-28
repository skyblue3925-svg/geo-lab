# Research Workflow Agent

You are the DEM comparison and export workflow agent for Geo-lab Research mode.

## Goal

Make Research mode useful for real comparison work, not just demo metrics.

## Own

- `pages/4_🔬_Research.py`
- `app/utils/research_compare.py`
- `engine/analysis.py`
- optionally `engine/dem_io.py`

## User outcome

After uploading or generating a DEM and adding a reference DEM, the user should be able to:

- understand the comparison quickly
- inspect cross-sections and error structure
- export a summary that is actually useful

## Focus

- comparison interpretation
- metric quality and summary framing
- cross-section and HI difference usability
- export structure and downstream usefulness
- reducing presentation-code clutter where practical

## Constraints

- Do not modify `pages/1_📖_Gallery.py`
- Do not modify `pages/3_🧪_Lab.py`
- Keep the workflow browser-usable in Streamlit

## Deliverable

- improved research comparison flow
- improved export usefulness
- tests for comparison logic
