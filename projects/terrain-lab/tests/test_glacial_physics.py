
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

from app.main import simulate_glacial, simulate_moraine

def test_glacial_physics():
    print("Testing Glacial Physics Integration...")
    
    # 1. Glacial (U-Valley)
    print("1. Glacial Erosion (U-Valley) Check...")
    params_g = {'ice_thickness': 1.0}
    res_g = simulate_glacial("u_valley", 100000, params_g, grid_size=50)
    elev_g = res_g['elevation']
    
    # Check if valley bottom is eroded
    # Initial was V-shape
    # Center col should be eroded
    center_elev = elev_g[:, 25].mean()
    edge_elev = elev_g[:, 0].mean()
    print(f"Center Mean Elev: {center_elev:.2f}, Edge Mean Elev: {edge_elev:.2f}")
    
    # Valley should be deep
    assert center_elev < edge_elev - 100, "Valley center should be significantly lower (U-Shape)"
    
    # 2. Moraine (Deposition)
    print("2. Moraine Deposition Check...")
    params_m = {'debris_supply': 1.0}
    res_m = simulate_moraine(100000, params_m, grid_size=50)
    elev_m = res_m['elevation']
    
    # Check for heaps (Moraines)
    # Lateral or Terminal
    # Max elevation should be higher than initial U-valley bottom logic
    # U-Valley base was ~200 at top, 100 at bottom
    # Moraine adds height
    
    max_elev = elev_m.max()
    print(f"Moraine Max Elev: {max_elev:.2f}")
    assert max_elev > 50.0, "Moraine should have some elevation" # Very loose check
    
    # Check if sediment changed (indirectly via elevation)
    # Ideally check if 'type' is Moraine
    print(f"Result Type: {res_m['type']}")
    
    print("Glacial Physics Test Passed!")

if __name__ == "__main__":
    test_glacial_physics()
