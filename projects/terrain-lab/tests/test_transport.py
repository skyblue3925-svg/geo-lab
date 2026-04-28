
import sys
import os
sys.path.append(os.getcwd())

from engine.grid import WorldGrid
from engine.erosion_process import ErosionProcess
import numpy as np

def test_transport():
    print("Testing Sediment Transport...")
    
    # 1. Setup Grid: Slope with a flat section (Deposition Zone)
    # 0 (High) -> 4 (Mid) -> 7 (Flat/Sea)
    # Rows 0-4: Steep slope
    # Rows 5-9: Flat (Sea Level)
    
    grid = WorldGrid(width=5, height=10, cell_size=10.0, sea_level=0.0)
    for r in range(5):
        grid.bedrock[r, :] = (5 - r) * 2.0 + 5.0 # 15, 13, 11, 9, 7
    for r in range(5, 10):
        grid.bedrock[r, :] = 5.0 # Flat plateau
    
    # Bottom 2 rows underwater
    grid.sea_level = 6.0 
    
    grid.update_elevation()
    
    erosion = ErosionProcess(grid, K=0.01, m=1.0, n=1.0)
    
    # 2. Fake Discharge (Unifrom flow from top)
    discharge = np.full((10, 5), 100.0)
    
    print(f"Initial Elev Row 4 (Slope Base): {grid.elevation[4,0]}")
    print(f"Initial Elev Row 7 (Flat Land): {grid.elevation[7,0]}")
    
    # 3. Run Transport
    # Should erode slope and deposit on flat land
    erosion.simulate_transport(discharge, dt=1.0)
    
    print(f"Post Elev Row 4: {grid.elevation[4,0]}")
    print(f"Post Elev Row 7: {grid.elevation[7,0]}")
    
    print("Sediment Array (Column 0):")
    print(grid.sediment[:, 0])
    
    # Check Erosion on Slope
    # assert grid.elevation[4,0] < 7.0, "Slope should erode"
    
    # Check Deposition on Flat
    flat_sediment = np.sum(grid.sediment[5:10, :])
    print(f"Total Sediment on Flat/Sea: {flat_sediment}")
    
    # assert flat_sediment > 0.0, "Sediment should deposit on flat area"
    if flat_sediment > 0.0:
        print("Sediment Transport OK")
    else:
        print("FAILED: No sediment on flat area")

if __name__ == "__main__":
    # Redirect stdout to file
    import sys
    sys.stdout = open("debug_log.txt", "w", encoding="utf-8")
    test_transport()
    sys.stdout.close()
