
import sys
import os
sys.path.append(os.getcwd())

from engine.grid import WorldGrid
from engine.erosion_process import ErosionProcess
import numpy as np

def test_erosion():
    print("Testing ErosionProcess...")
    
    # 1. Test Hillslope Diffusion
    grid = WorldGrid(width=5, height=5, cell_size=1.0)
    grid.elevation[:] = 0.0
    grid.elevation[2, 2] = 10.0 # Spike in center
    
    erosion = ErosionProcess(grid, D=0.1)
    
    print(f"Initial Max Elev: {np.max(grid.elevation)}")
    erosion.hillslope_diffusion(dt=1.0)
    print(f"Post-Diffusion Max Elev: {np.max(grid.elevation)}")
    
    assert grid.elevation[2, 2] < 10.0, "Spike should lower"
    assert grid.elevation[2, 3] > 0.0, "Neighbor should rise"
    print("Diffusion OK")
    
    # 2. Test Stream Power Erosion
    grid2 = WorldGrid(width=5, height=5, cell_size=10.0)
    # Simple slope
    for r in range(5):
        grid2.elevation[r, :] = (10 - r) * 10
    
    erosion2 = ErosionProcess(grid2, K=1e-3, m=0.5, n=1.0)
    
    # Fake discharge (increasing downstream)
    discharge = np.zeros((5, 5))
    for r in range(5):
        discharge[r, :] = (r + 1) * 100
        
    old_elev = grid2.elevation.copy()
    erosion2.stream_power_erosion(discharge, dt=10.0)
    
    # Check erosion happened
    diff = old_elev - grid2.elevation
    
    # Check downstream eroded more (higher Q)
    # Row 4 (bottom) should erode more than Row 0 (top)
    # Both have same slope (roughly), but Q is 500 vs 100.
    # Actually Row 4 is bottom edge, calculation might be tricky with gradient boundary.
    # Check Row 3 vs Row 0.
    assert diff[3, 2] > diff[0, 2], f"Downstream should erode more: {diff[3,2]} vs {diff[0,2]}"
    
    print("Stream Power Erosion OK")
    print("All ErosionProcess tests passed!")

if __name__ == "__main__":
    test_erosion()
