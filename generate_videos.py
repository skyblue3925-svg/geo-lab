"""
🎬 지형 형성 과정 영상 생성기
Geo-lab의 애니메이션 함수를 활용하여 MP4 영상을 생성합니다.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import cm
import os
import sys

# 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.ideal_landforms import ANIMATED_LANDFORM_GENERATORS

# 출력 디렉토리
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "cinematic")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_landform_video(
    landform_key: str,
    output_filename: str = None,
    grid_size: int = 100,
    num_frames: int = 60,
    fps: int = 15,
    duration_seconds: int = 4,
    title: str = None,
    view_elev: int = 30,
    view_azim: int = -60
):
    """
    지형 형성 과정을 MP4 영상으로 생성합니다.
    
    Args:
        landform_key: 지형 키 (예: 'fjord', 'barchan', 'caldera')
        output_filename: 출력 파일명 (없으면 자동 생성)
        grid_size: 그리드 해상도
        num_frames: 프레임 수
        fps: 초당 프레임 수
        duration_seconds: 영상 길이 (초)
        title: 영상 제목
        view_elev: 3D 뷰 고도각
        view_azim: 3D 뷰 방위각
    """
    if landform_key not in ANIMATED_LANDFORM_GENERATORS:
        print(f"❌ 지형 '{landform_key}'에 대한 애니메이션 함수가 없습니다.")
        print(f"사용 가능: {list(ANIMATED_LANDFORM_GENERATORS.keys())}")
        return None
    
    anim_func = ANIMATED_LANDFORM_GENERATORS[landform_key]
    
    if output_filename is None:
        output_filename = f"{landform_key}_formation.mp4"
    
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    if title is None:
        title = f"{landform_key.replace('_', ' ').title()} 형성 과정"
    
    print(f"🎬 '{landform_key}' 영상 생성 시작...")
    print(f"   해상도: {grid_size}x{grid_size}, 프레임: {num_frames}, FPS: {fps}")
    
    # Figure 설정
    fig = plt.figure(figsize=(12, 8), facecolor='white')
    ax = fig.add_subplot(111, projection='3d')
    
    # 단계별 데이터 생성
    stages = np.linspace(0, 1, num_frames)
    
    def update(frame_idx):
        ax.clear()
        stage = stages[frame_idx]
        
        # 지형 생성
        try:
            elevation, metadata = anim_func(grid_size, stage, return_metadata=True)
            stage_desc = metadata.get('stage_description', f'{int(stage*100)}% 완료')
        except TypeError:
            elevation = anim_func(grid_size, stage)
            stage_desc = f'{int(stage*100)}% 완료'
        
        # 그리드 생성
        x = np.arange(grid_size)
        y = np.arange(grid_size)
        X, Y = np.meshgrid(x, y)
        
        # 3D 표면 그리기
        surf = ax.plot_surface(
            X, Y, elevation,
            cmap='terrain',
            linewidth=0,
            antialiased=True,
            alpha=0.9
        )
        
        # 물 표시 (음수 고도)
        water_level = 0
        if elevation.min() < water_level:
            water_mask = elevation < water_level
            water_surface = np.where(water_mask, water_level, np.nan)
            ax.plot_surface(
                X, Y, water_surface,
                color='steelblue',
                alpha=0.6
            )
        
        # 축 설정
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('고도 (m)')
        ax.set_title(f"{title}\n{stage_desc}", fontsize=14, fontweight='bold')
        ax.view_init(elev=view_elev, azim=view_azim)
        
        # 진행률 표시
        progress = (frame_idx + 1) / num_frames * 100
        print(f"\r   진행률: {progress:.0f}%", end='', flush=True)
        
        return [surf]
    
    # 애니메이션 생성
    anim = animation.FuncAnimation(
        fig, update,
        frames=num_frames,
        interval=1000 // fps,
        blit=False
    )
    
    # MP4로 저장
    print(f"\n   MP4 인코딩 중...")
    try:
        writer = animation.FFMpegWriter(fps=fps, metadata={'title': title})
        anim.save(output_path, writer=writer, dpi=100)
        print(f"✅ 저장 완료: {output_path}")
    except Exception as e:
        print(f"⚠️ FFmpeg 없음. GIF로 저장 시도...")
        gif_path = output_path.replace('.mp4', '.gif')
        try:
            anim.save(gif_path, writer='pillow', fps=fps)
            print(f"✅ GIF 저장 완료: {gif_path}")
            output_path = gif_path
        except Exception as e2:
            print(f"❌ 저장 실패: {e2}")
            output_path = None
    
    plt.close(fig)
    return output_path


def create_all_featured_videos():
    """우선 제작 지형 5종의 영상을 모두 생성합니다."""
    
    featured_landforms = {
        'fjord': {'title': '🧊 피오르드 형성 과정', 'view_elev': 35, 'view_azim': -45},
        'delta': {'title': '🌊 삼각주 형성 과정', 'view_elev': 45, 'view_azim': -60},
        'barchan': {'title': '🏜️ 바르한 사구 이동', 'view_elev': 25, 'view_azim': -30},
        'caldera': {'title': '🌋 칼데라 형성 과정', 'view_elev': 30, 'view_azim': -60},
        'sea_arch': {'title': '🏖️ 해식아치 형성', 'view_elev': 20, 'view_azim': -45},
    }
    
    results = {}
    
    for key, config in featured_landforms.items():
        print(f"\n{'='*50}")
        output = create_landform_video(
            landform_key=key,
            title=config['title'],
            view_elev=config['view_elev'],
            view_azim=config['view_azim'],
            grid_size=80,
            num_frames=45,
            fps=12
        )
        results[key] = output
    
    print(f"\n{'='*50}")
    print("📊 생성 결과:")
    for key, path in results.items():
        status = "✅" if path else "❌"
        print(f"   {status} {key}: {path}")
    
    return results


def create_all_high_res_gifs(num_frames=200, grid_size=120):
    """모든 애니메이션 지형을 고해상도 GIF로 생성합니다."""
    
    print(f"🎬 고해상도 GIF 생성 시작 (프레임: {num_frames}, 해상도: {grid_size})")
    print(f"📁 출력 폴더: {OUTPUT_DIR}")
    
    results = {}
    
    # 모든 애니메이션 지형
    for key in sorted(ANIMATED_LANDFORM_GENERATORS.keys()):
        print(f"\n{'='*60}")
        output = create_landform_video(
            landform_key=key,
            output_filename=f"{key}_hires.gif",
            grid_size=grid_size,
            num_frames=num_frames,
            fps=20,
            title=f"{key.replace('_', ' ').title()} 형성 과정"
        )
        results[key] = output
    
    print(f"\n{'='*60}")
    print("📊 전체 생성 결과:")
    success = sum(1 for v in results.values() if v)
    print(f"   성공: {success}/{len(results)}")
    for key, path in results.items():
        status = "✅" if path else "❌"
        print(f"   {status} {key}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='지형 형성 영상 생성기')
    parser.add_argument('--landform', '-l', type=str, help='생성할 지형 (예: fjord, barchan)')
    parser.add_argument('--all', '-a', action='store_true', help='모든 주요 지형 생성 (45프레임)')
    parser.add_argument('--hires', action='store_true', help='모든 지형 고해상도 생성 (200프레임)')
    parser.add_argument('--frames', '-f', type=int, default=200, help='프레임 수 (기본: 200)')
    parser.add_argument('--list', action='store_true', help='사용 가능한 지형 목록')
    
    args = parser.parse_args()
    
    if args.list:
        print("🗺️ 사용 가능한 지형:")
        for key in sorted(ANIMATED_LANDFORM_GENERATORS.keys()):
            print(f"   - {key}")
    elif args.hires:
        create_all_high_res_gifs(num_frames=args.frames)
    elif args.all:
        create_all_featured_videos()
    elif args.landform:
        create_landform_video(args.landform, num_frames=args.frames)
    else:
        print("사용법:")
        print("  python generate_videos.py --landform fjord       # 특정 지형")
        print("  python generate_videos.py --landform fjord -f 200  # 200프레임")
        print("  python generate_videos.py --all                  # 주요 5종 (45프레임)")
        print("  python generate_videos.py --hires                # 전체 고해상도 (200프레임)")
        print("  python generate_videos.py --list                 # 지형 목록")
