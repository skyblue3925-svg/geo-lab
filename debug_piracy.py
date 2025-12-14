
import numpy as np
import plotly.graph_objects as go

# Mock functions from main.py
def simulate_stream_piracy(time_years: int, params: dict, grid_size: int = 100):
    """하천쟁탈 시뮬레이션 - 교과서적 이상적 모습"""
    x = np.linspace(0, 1000, grid_size)
    y = np.linspace(0, 1000, grid_size)
    X, Y = np.meshgrid(x, y)
    elevation = 150 - Y * 0.1
    ridge_x = 500
    ridge = 20 * np.exp(-((X - ridge_x)**2) / (80**2))
    elevation += ridge
    river1_x = 300
    river1_valley = 30 * np.exp(-((X - river1_x)**2) / (40**2))
    elevation -= river1_valley
    river2_x = 700
    erosion_diff = params.get('erosion_diff', 0.7)
    river2_depth = 50 * erosion_diff
    river2_valley = river2_depth * np.exp(-((X - river2_x)**2) / (50**2))
    elevation -= river2_valley
    
    # ... logic ...
    # Simplified logic for t=5000 (not captured)
    return {'elevation': elevation, 'captured': False}

def render_terrain_plotly_debug(elevation):
    print(f"Elevation stats: Min={elevation.min()}, Max={elevation.max()}, NaNs={np.isnan(elevation).sum()}")
    
    dy, dx = np.gradient(elevation)
    print(f"Gradient stats: dx_NaN={np.isnan(dx).sum()}, dy_NaN={np.isnan(dy).sum()}")
    
    slope = np.sqrt(dx**2 + dy**2)
    print(f"Slope stats: Min={slope.min()}, Max={slope.max()}, NaNs={np.isnan(slope).sum()}")
    
    biome = np.zeros_like(elevation)
    biome[:] = 1
    # ...
    noise = np.random.normal(0, 0.2, elevation.shape)
    biome_noisy = np.clip(biome + noise, 0, 3)
    print(f"Biome Noisy stats: Min={biome_noisy.min()}, Max={biome_noisy.max()}, NaNs={np.isnan(biome_noisy).sum()}")
    
    realistic_colorscale = [
        [0.0, '#E6C288'], [0.25, '#E6C288'], 
        [0.25, '#2E8B57'], [0.5, '#2E8B57'], 
        [0.5, '#696969'], [0.75, '#696969'], 
        [0.75, '#FFFFFF'], [1.0, '#FFFFFF']
    ]
    print("Colorscale:", realistic_colorscale)

if __name__ == "__main__":
    res = simulate_stream_piracy(5000, {'erosion_diff': 0.7})
    elev = res['elevation']
    render_terrain_plotly_debug(elev)
