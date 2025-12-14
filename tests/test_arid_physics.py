
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

from app.main import simulate_arid

def test_arid_physics():
    print("Testing Arid Physics Integration...")
    
    # 1. Barchan Dunes (Eolian Transport)
    print("1. Barchan Dune Check...")
    params_b = {'wind_speed': 1.0}
    res_b = simulate_arid("barchan", 50, params_b, grid_size=50) # Short steps
    elev_b = res_b['elevation']
    
    # Check if dunes exist (Max elev > 5)
    max_dune = elev_b.max()
    print(f"Dune Max Elev: {max_dune:.2f}")
    assert max_dune > 5.0, "Dunes should have elevation"
    
    # 2. Mesa (Differential Erosion)
    print("2. Mesa Check...")
    params_m = {'rock_hardness': 1.0}
    res_m = simulate_arid("mesa", 1000, params_m, grid_size=50)
    elev_m = res_m['elevation']
    
    # Check if plateau top remains (Hard caprock)
    # Center should be high
    center_elev = elev_m[25, 25] # 50x50 grid center
    print(f"Mesa Center Elev: {center_elev:.2f}")
    assert center_elev > 40.0, "Mesa top should remain high due to hard caprock"
    
    print("Arid Physics Test Passed!")

if __name__ == "__main__":
    test_arid_physics()
