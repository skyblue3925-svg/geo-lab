import numpy as np
from engine.grid import WorldGrid
from engine.system import EarthSystem

def test_fan_mechanism():
    print("Testing Project Genesis Alluvial Fan Mechanism...")
    
    # 1. Setup Mini Grid (20x20)
    grid = WorldGrid(width=20, height=20, cell_size=10.0)
    
    # Slope N->S
    for r in range(20):
        grid.bedrock[r, :] = 20.0 - r * 0.5 # 20m -> 10m
        
    grid.update_elevation()
    
    # 2. Setup Engine
    engine = EarthSystem(grid)
    engine.erosion.K = 0.001 # Low K to force deposition
    
    # 3. Step with sediment source
    # Source at (2, 10)
    source_y, source_x = 2, 10
    amount = 100.0
    
    settings = {
        'precipitation': 0.0,
        'rain_source': (0, 10, 2, 10.0), # Rain at top
        'sediment_source': (source_y, source_x, 1, amount) # Sediment at source
    }
    
    print(f"Initial Max Sediment: {grid.sediment.max()}")
    
    # Run 10 steps
    np.set_printoptions(precision=4, suppress=True)
    for i in range(10):
        engine.step(dt=1.0, settings=settings)
        print(f"Step {i+1}:")
        print(f"  Max Sediment: {grid.sediment.max():.6f}")
        print(f"  Max Discharge: {grid.discharge.max():.6f}")
        print(f"  Max Elev: {grid.elevation.max():.6f}")
        
    if grid.sediment.max() > 0:
        print("SUCCESS: Sediment is depositing.")
        print("Sample Sediment Grid (Center):")
        print(grid.sediment[0:5, 8:13])
    else:
        print("FAILURE: No sediment deposited.")

if __name__ == "__main__":
    test_fan_mechanism()
