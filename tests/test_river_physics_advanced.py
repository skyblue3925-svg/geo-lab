
import sys
import os
import numpy as np
import unittest.mock

# Mock Streamlit
mock_st = unittest.mock.MagicMock()
def pass_through_decorator(*args, **kwargs):
    def decorator(f):
        return f
    return decorator
mock_st.cache_data = pass_through_decorator
sys.modules["streamlit"] = mock_st

# Add path
sys.path.insert(0, os.getcwd())

from app.main import simulate_braided_stream, simulate_river_terrace

def test_river_physics_advanced():
    print("Testing Advanced River Physics (Braided & Terrace)...")
    
    # 1. Braided Stream Test
    print("1. Braided Stream Check...")
    params_br = {'n_channels': 5, 'sediment': 0.8}
    res_br = simulate_braided_stream(100000, params_br, grid_size=50)
    elev_br = res_br['elevation']
    
    # Check for roughness (braiding creates noise/channel bars)
    roughness = np.std(elev_br[25, 10:40])
    print(f"Braided Roughness: {roughness:.4f}")
    assert roughness > 0.0, "Braided stream should have topographic variation (channels)"
    
    # 2. River Terrace Test
    print("2. River Terrace Check...")
    params_rt = {'uplift': 0.5, 'n_terraces': 3}
    res_rt = simulate_river_terrace(100000, params_rt, grid_size=50)
    elev_rt = res_rt['elevation']
    heights = res_rt['heights']
    
    print(f"Terrace Heights recorded: {heights}")
    
    # Check for steps/terraces (profile analysis)
    # Center should be lowest (current river)
    center = 25
    mid_elev = elev_rt[25, center]
    
    # Banks should be higher
    bank_elev = elev_rt[25, 5]
    
    print(f"River Bed: {mid_elev:.2f}, Bank (Terrace): {bank_elev:.2f}")
    assert bank_elev > mid_elev + 1.0, "River bed should be lower than terraces due to incision"
    
    print("Advanced River Physics Test Passed!")

if __name__ == "__main__":
    test_river_physics_advanced()
