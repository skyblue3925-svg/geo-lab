"""
🖼️ 지형 프레임 이미지 추출기
200프레임에서 5프레임 간격으로 이미지를 추출하여 지형별 폴더에 저장합니다.
"""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
import sys

# 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.ideal_landforms import ANIMATED_LANDFORM_GENERATORS

# 출력 디렉토리
OUTPUT_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "frames")
os.makedirs(OUTPUT_BASE, exist_ok=True)

# 지형별 최적 카메라 각도
LANDFORM_CAMERAS = {
    # 하천 지형
    'alluvial_fan': {'elev': 45, 'azim': -45, 'title': '선상지'},
    'braided_river': {'elev': 50, 'azim': -60, 'title': '망상하천'},
    'delta': {'elev': 55, 'azim': -45, 'title': '삼각주'},
    'free_meander': {'elev': 40, 'azim': -50, 'title': '자유곡류'},
    'incised_meander': {'elev': 35, 'azim': -55, 'title': '감입곡류'},
    'v_valley': {'elev': 30, 'azim': -60, 'title': 'V자곡'},
    'waterfall': {'elev': 25, 'azim': -45, 'title': '폭포'},
    'perched_river': {'elev': 35, 'azim': -50, 'title': '천정천'},
    
    # 삼각주 유형
    'arcuate_delta': {'elev': 55, 'azim': -45, 'title': '호상삼각주'},
    'bird_foot_delta': {'elev': 60, 'azim': -40, 'title': '조족상삼각주'},
    'cuspate_delta': {'elev': 55, 'azim': -45, 'title': '첨두상삼각주'},
    
    # 빙하 지형
    'cirque': {'elev': 30, 'azim': -45, 'title': '권곡'},
    'drumlin': {'elev': 25, 'azim': -30, 'title': '드럼린'},
    'fjord': {'elev': 30, 'azim': -50, 'title': '피오르드'},
    'horn': {'elev': 25, 'azim': -45, 'title': '호른'},
    'moraine': {'elev': 35, 'azim': -55, 'title': '빙퇴석'},
    'u_valley': {'elev': 30, 'azim': -60, 'title': 'U자곡'},
    
    # 화산 지형
    'caldera': {'elev': 35, 'azim': -45, 'title': '칼데라'},
    'crater_lake': {'elev': 40, 'azim': -50, 'title': '칼데라호'},
    'shield_volcano': {'elev': 25, 'azim': -45, 'title': '순상화산'},
    'stratovolcano': {'elev': 30, 'azim': -50, 'title': '성층화산'},
    
    # 카르스트 지형
    'karst_doline': {'elev': 40, 'azim': -45, 'title': '돌리네'},
    'tower_karst': {'elev': 25, 'azim': -40, 'title': '탑카르스트'},
    'uvala_doline': {'elev': 45, 'azim': -50, 'title': '우발라'},
    
    # 건조 지형
    'barchan': {'elev': 20, 'azim': -35, 'title': '바르한사구'},
    'mesa_butte': {'elev': 25, 'azim': -45, 'title': '메사뷰트'},
    'star_dune': {'elev': 30, 'azim': -45, 'title': '성사구'},
    'transverse_dune': {'elev': 25, 'azim': -30, 'title': '횡사구'},
    'wadi': {'elev': 35, 'azim': -50, 'title': '와디'},
    
    # 해안 지형
    'coastal_cliff': {'elev': 25, 'azim': -45, 'title': '해안절벽'},
    'sea_arch': {'elev': 20, 'azim': -40, 'title': '해식아치'},
    'spit_lagoon': {'elev': 45, 'azim': -55, 'title': '사취석호'},
    'tombolo': {'elev': 40, 'azim': -50, 'title': '육계사주'},
}


def extract_frames(
    landform_key: str,
    num_frames: int = 200,
    frame_interval: int = 5,
    grid_size: int = 120,
    dpi: int = 150
):
    """
    지형 형성 과정의 프레임을 이미지로 추출합니다.
    
    Args:
        landform_key: 지형 키
        num_frames: 총 프레임 수
        frame_interval: 추출 간격 (5면 5프레임마다 추출)
        grid_size: 그리드 해상도
        dpi: 이미지 해상도
    """
    if landform_key not in ANIMATED_LANDFORM_GENERATORS:
        print(f"❌ 지형 '{landform_key}'에 대한 애니메이션 함수가 없습니다.")
        return None
    
    # 출력 폴더 생성
    output_dir = os.path.join(OUTPUT_BASE, landform_key)
    os.makedirs(output_dir, exist_ok=True)
    
    anim_func = ANIMATED_LANDFORM_GENERATORS[landform_key]
    camera = LANDFORM_CAMERAS.get(landform_key, {'elev': 30, 'azim': -45, 'title': landform_key})
    
    print(f"🖼️ '{landform_key}' 프레임 추출 시작...")
    print(f"   총 프레임: {num_frames}, 간격: {frame_interval}, 추출 수: {num_frames // frame_interval}")
    print(f"   카메라: elev={camera['elev']}, azim={camera['azim']}")
    
    stages = np.linspace(0, 1, num_frames)
    extracted_count = 0
    
    for frame_idx in range(0, num_frames, frame_interval):
        stage = stages[frame_idx]
        
        # 지형 생성
        try:
            elevation, metadata = anim_func(grid_size, stage, return_metadata=True)
            stage_desc = metadata.get('stage_description', '')
        except TypeError:
            elevation = anim_func(grid_size, stage)
            stage_desc = ''
        
        # 그리드 생성
        x = np.arange(grid_size)
        y = np.arange(grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Figure 생성
        fig = plt.figure(figsize=(10, 8), facecolor='white')
        ax = fig.add_subplot(111, projection='3d')
        
        # 3D 표면 그리기
        ax.plot_surface(
            X, Y, elevation,
            cmap='terrain',
            linewidth=0,
            antialiased=True,
            alpha=0.95
        )
        
        # 물 표시
        water_level = 0
        if elevation.min() < water_level:
            water_mask = elevation < water_level
            water_surface = np.where(water_mask, water_level, np.nan)
            ax.plot_surface(X, Y, water_surface, color='steelblue', alpha=0.6)
        
        # 축 설정
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('고도 (m)')
        
        title = f"{camera['title']} 형성 과정 - {int(stage*100)}%"
        if stage_desc:
            title += f"\n{stage_desc}"
        ax.set_title(title, fontsize=12, fontweight='bold')
        
        ax.view_init(elev=camera['elev'], azim=camera['azim'])
        
        # 저장
        filename = f"frame_{frame_idx:03d}_{int(stage*100):03d}pct.png"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        extracted_count += 1
        progress = (frame_idx + frame_interval) / num_frames * 100
        print(f"\r   진행률: {min(progress, 100):.0f}% ({extracted_count}개 추출)", end='', flush=True)
    
    print(f"\n✅ 완료: {output_dir}")
    print(f"   총 {extracted_count}개 이미지 저장")
    
    return output_dir


def extract_all_landform_frames(num_frames=200, frame_interval=5, grid_size=120):
    """모든 지형의 프레임을 추출합니다."""
    
    print(f"🖼️ 전체 지형 프레임 추출 시작")
    print(f"   설정: {num_frames}프레임, {frame_interval}간격, {grid_size}해상도")
    print(f"   출력: {OUTPUT_BASE}")
    print(f"   지형당 이미지 수: {num_frames // frame_interval}개")
    
    results = {}
    
    for i, key in enumerate(sorted(ANIMATED_LANDFORM_GENERATORS.keys())):
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(ANIMATED_LANDFORM_GENERATORS)}] {key}")
        output = extract_frames(
            landform_key=key,
            num_frames=num_frames,
            frame_interval=frame_interval,
            grid_size=grid_size
        )
        results[key] = output
    
    print(f"\n{'='*60}")
    print("📊 전체 추출 결과:")
    success = sum(1 for v in results.values() if v)
    print(f"   성공: {success}/{len(results)}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='지형 프레임 이미지 추출기')
    parser.add_argument('--landform', '-l', type=str, help='추출할 지형')
    parser.add_argument('--all', '-a', action='store_true', help='모든 지형 추출')
    parser.add_argument('--frames', '-f', type=int, default=200, help='총 프레임 수')
    parser.add_argument('--interval', '-i', type=int, default=5, help='추출 간격')
    parser.add_argument('--list', action='store_true', help='지형 목록')
    
    args = parser.parse_args()
    
    if args.list:
        print("🗺️ 사용 가능한 지형:")
        for key in sorted(ANIMATED_LANDFORM_GENERATORS.keys()):
            camera = LANDFORM_CAMERAS.get(key, {})
            title = camera.get('title', key)
            print(f"   - {key} ({title})")
    elif args.all:
        extract_all_landform_frames(
            num_frames=args.frames,
            frame_interval=args.interval
        )
    elif args.landform:
        extract_frames(
            args.landform,
            num_frames=args.frames,
            frame_interval=args.interval
        )
    else:
        print("사용법:")
        print("  python extract_frames.py --landform fjord      # 특정 지형")
        print("  python extract_frames.py --all                 # 모든 지형")
        print("  python extract_frames.py --all -f 200 -i 5     # 200프레임, 5간격")
        print("  python extract_frames.py --list                # 지형 목록")
