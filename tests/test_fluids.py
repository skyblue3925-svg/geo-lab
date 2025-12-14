
import sys
import os
sys.path.append(os.getcwd())

from engine.grid import WorldGrid
from engine.fluids import HydroKernel
import numpy as np

def test_hydro():
    print("Testing HydroKernel...")
    
    # 1. Setup Grid
    grid = WorldGrid(width=5, height=5, cell_size=10.0, sea_level=0.0)
    # create a simple ramp
    for r in range(5):
        grid.bedrock[r, :] = (4 - r) * 10
    grid.update_elevation()
    
    hydro = HydroKernel(grid)
    
    # 2. Test Flow Routing
    # Rain 1.0 on all cells
    discharge = hydro.route_flow_d8(precipitation=1.0)
    
    # Top row (index 0) should have base rain only
    # cell area = 100 m^2
    # precip = 1.0 m
    # base Q = 100 m^3/s
    assert np.allclose(discharge[0, :], 100.0)
    
    # Bottom row (index 4) should accumulate all upstream
    # Total accumulated discharge in the bottom row should equal total precipitation volume on the grid
    # Grid 5x5 cells. Cell area 100. Precip 1.0. Total vol = 2500.
    total_discharge_out = np.sum(discharge[4, :])
    assert np.isclose(total_discharge_out, 2500.0), f"Expected 2500.0, got {total_discharge_out}"
    print("Flow Routing OK (Mass Conserved)")
    
    # 3. Test Water Depth
    depth = hydro.calculate_water_depth(discharge)
    assert np.all(depth > 0)
    print("Water Depth OK")
    
    # 4. Test Inundation
    grid.sea_level = 15.0 # Rows 3,4 (elev 10, 0) should be underwater
    hydro.simulate_inundation()
    
    # Check bottom row (expected depth = 15 - 0 = 15m)
    assert np.isclose(grid.water_depth[4, 0], 15.0)
    # Top row (elev 40) should be dry (depth from river only, or 0 if we reset)
    # Here we didn't reset water_depth, so it might have river depth.
    # But it definitely shouldn't be SEA depth.
    
    print("Inundation OK")
    print("All HydroKernel tests passed!")

if __name__ == "__main__":
    test_hydro()
