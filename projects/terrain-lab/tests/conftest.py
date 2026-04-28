import os

os.environ.setdefault("MPLBACKEND", "Agg")

try:
    import matplotlib

    matplotlib.use("Agg", force=True)
except Exception:
    pass
