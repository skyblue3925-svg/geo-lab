
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

from app.main import simulate_coastal

def test_coastal_physics():
    print("Testing Coastal Physics Integration...")
    
    # Test Parameters
    # erosion (Cliff)
    params = {'wave_height': 3.0, 'rock_resistance': 0.2}
    res_cliff = simulate_coastal("erosion", 100000, params, grid_size=50)
    elev_cliff = res_cliff['elevation']
    
    # Check if cliff retreated
    # Initial Headland x=25, width=16. (grid 50)
    # Check center of headland
    center = 25
    
    # Originally Headland area at Y < 30 (approx) was elevation 50
    # Eroded area should be lower
    # Coastline is Y ~ 15
    
    # Just check if elevation changed at the coastline
    # Before: Y=15, X=25 is Headland (Elev 50)
    # After: Should be lower (Wave cut)
    
    current_elev = elev_cliff[15, 25]
    print(f"Headland Coast Elev: {current_elev:.2f}")
    assert current_elev < 45.0, "Headland should be eroded by waves"
    
    print("Coastal Physics Test Passed!")

if __name__ == "__main__":
    test_coastal_physics()
