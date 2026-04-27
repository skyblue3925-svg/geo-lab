
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

from app.main import simulate_alluvial_fan

def test_fan_physics():
    print("Testing Alluvial Fan Physics Integration...")
    
    # Test Parameters
    params = {'slope': 0.5, 'sediment': 0.8}
    time_years = 100000
    
    # Run Simulation
    result = simulate_alluvial_fan(time_years, params, grid_size=50)
    
    # Check outputs
    assert 'elevation' in result
    assert 'area' in result
    assert result['elevation'].shape == (50, 50)
    
    elev = result['elevation']
    
    # Verification: Fan should form below the canyon
    # Canyon is Top Center ~row 0-10
    # Fan is below ~row 10
    
    apex_row = int(50 * 0.2)
    center = 25
    
    # Check if sediment accumulated below apex
    fan_area = elev[apex_row+5:apex_row+15, center-5:center+5]
    fan_max = fan_area.max()
    
    # Compare to surrounding plain
    plain_area = elev[apex_row+5:apex_row+15, 0:5]
    plain_max = plain_area.max()
    
    print(f"Fan Max Elev: {fan_max:.2f}")
    print(f"Plain Max Elev: {plain_max:.2f}")
    
    assert fan_max > plain_max + 1.0, "Fan should be higher than plain"
    
    print("Alluvial Fan Physics Test Passed!")

if __name__ == "__main__":
    test_fan_physics()
