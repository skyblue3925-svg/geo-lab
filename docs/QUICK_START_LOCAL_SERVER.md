# Geo-lab Local Server Quick Start

## One command

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab"
.\run_geo_lab.ps1 -KillPortOwner
```

If `.venv` is missing or references an old Python installation:

```powershell
.\run_geo_lab.ps1 -BootstrapVenv
```

## Manual command

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab"
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8501
```

## Verify

- Open `http://localhost:8501`
- If browser does not open, check:

```powershell
netstat -ano | Select-String 8501
```

## Common errors

- `ModuleNotFoundError: No module named 'plotly'`
  - Run with `.venv` python only.
  - Confirm with:

```powershell
.\.venv\Scripts\python.exe -c "import plotly, streamlit; print(plotly.__version__, streamlit.__version__)"
```

- `Port 8501 is already in use`
  - Use `-KillPortOwner` option or run with another port:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

- `Unable to create process ... Python311`
  - The old virtualenv points to a removed Python install.
  - Recreate it with:

```powershell
.\run_geo_lab.ps1 -BootstrapVenv
```
