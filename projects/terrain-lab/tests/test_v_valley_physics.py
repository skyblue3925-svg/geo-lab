
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

from app.main import simulate_v_valley

def test_v_valley_physics():
    print("Testing V-Valley Physics Integration...")
    
    # Test Parameters
    params = {'K': 0.0001, 'rock_hardness': 0.5}
    time_years = 100000
    
    # Run Simulation
    result = simulate_v_valley("stream_power", time_years, params, grid_size=50)
    
    # Check outputs
    assert 'elevation' in result
    assert 'depth' in result
    assert result['elevation'].shape == (50, 50)
    
    elev = result['elevation']
    center = 25
    
    # V-Shape verification (Edges > Center)
    edge_mean = (elev[:, 0].mean() + elev[:, -1].mean()) / 2
    center_mean = elev[:, center].mean()
    
    print(f"Edge Mean Elev: {edge_mean:.2f}")
    print(f"Center Mean Elev: {center_mean:.2f}")
    
    assert edge_mean > center_mean, "Valley should be lower in the center"
    
    print("V-Valley Physics Test Passed!")

if __name__ == "__main__":
    test_v_valley_physics()
