
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

from app.main import simulate_karst, simulate_volcanic

def test_special_physics():
    print("Testing Special Landforms Physics (Karst, Volcano)...")
    
    # 1. Karst
    print("1. Karst Dissolution Check...")
    params_k = {'co2': 1.0, 'rainfall': 1.0}
    res_k = simulate_karst("doline", 100000, params_k, grid_size=50)
    elev_k = res_k['elevation']
    
    # Check for holes (Sinkholes)
    # Original Base Height = 100
    min_elev = elev_k.min()
    print(f"Karst Min Elevation: {min_elev:.2f}")
    assert min_elev < 95.0, "Sinkholes should form via dissolution"
    
    # 2. Volcano
    print("2. Volcano Growth Check...")
    params_v = {'eruption_rate': 1.0}
    res_v = simulate_volcanic("strato", 100000, params_v, grid_size=50)
    elev_v = res_v['elevation']
    
    # Check for growth
    # Base = 50
    max_elev = elev_v.max()
    print(f"Volcano Max Elevation: {max_elev:.2f}")
    assert max_elev > 60.0, "Volcano should grow via lava accumulation"
    
    print("Special Physics Test Passed!")

if __name__ == "__main__":
    test_special_physics()
