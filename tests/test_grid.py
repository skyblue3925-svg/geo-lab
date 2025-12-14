
import sys
import os
sys.path.append(os.getcwd())

from engine.grid import WorldGrid
import numpy as np

def test_grid():
    print("Testing WorldGrid...")
    grid = WorldGrid(width=10, height=10, cell_size=10.0, sea_level=0.0)
    
    # Check initialization
    assert grid.elevation.shape == (10, 10)
    print("Initialization OK")
    
    # Check uplift
    grid.apply_uplift(1.0, dt=10.0)
    assert np.allclose(grid.bedrock, 10.0)
    assert np.allclose(grid.elevation, 10.0)
    print("Uplift OK")
    
    # Check sediment
    grid.add_sediment(np.full((10, 10), 5.0))
    assert np.allclose(grid.sediment, 5.0)
    assert np.allclose(grid.elevation, 15.0)  # 10 bedrock + 5 sediment
    print("Sediment OK")
    
    # Check gradient
    grid.elevation[0, 0] = 100.0  # High point
    slope, aspect = grid.get_gradient()
    print(f"Max Slope: {np.max(slope):.2f}")
    
    print("All WorldGrid tests passed!")

if __name__ == "__main__":
    test_grid()
