
import sys
import os
import numpy as np
import unittest.mock

# Mock Streamlit with pass-through decorator
mock_st = unittest.mock.MagicMock()
def pass_through_decorator(*args, **kwargs):
    def decorator(f):
        return f
    return decorator
mock_st.cache_data = pass_through_decorator
sys.modules["streamlit"] = mock_st

# Add path
sys.path.insert(0, os.getcwd())

from app.main import simulate_delta

def test_simulate_delta_integration():
    print("Testing simulate_delta integration...")
    
    # 1. Test River Dominated
    params_river = {'river': 0.8, 'wave': 0.1}
    result_river = simulate_delta("orton", 1000, params_river, grid_size=50)
    
    assert 'elevation' in result_river
    assert result_river['elevation'].shape == (50, 50)
    print("River dominated run: OK")
    
    # 2. Test Wave Dominated
    params_wave = {'river': 0.2, 'wave': 0.9}
    result_wave = simulate_delta("bhattacharya", 1000, params_wave, grid_size=50)
    
    assert 'elevation' in result_wave
    print("Wave dominated run: OK")
    
    print("Integration Test Passed!")

if __name__ == "__main__":
    test_simulate_delta_integration()
