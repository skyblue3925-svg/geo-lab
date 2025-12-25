"""
🛠️ 캐싱 유틸리티
Geo-Lab 성능 최적화를 위한 캐싱 헬퍼
"""
import streamlit as st
import hashlib
import numpy as np
from typing import Any, Callable, Tuple
from functools import wraps


def get_cache_key(*args, **kwargs) -> str:
    """캐시 키 생성
    
    Args:
        *args: 캐시 키에 포함할 인자들
        **kwargs: 캐시 키에 포함할 키워드 인자들
        
    Returns:
        MD5 해시 문자열
    """
    key_str = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_str.encode()).hexdigest()[:16]


def cache_landform_data(landform_name: str, grid_size: int, stage: float, 
                        generator_func: Callable) -> Tuple[np.ndarray, dict]:
    """지형 데이터 캐싱
    
    세션 상태를 활용하여 동일한 지형/크기/단계의 데이터를 캐싱합니다.
    
    Args:
        landform_name: 지형 이름 (예: 'delta', 'alluvial_fan')
        grid_size: 그리드 크기
        stage: 형성 단계 (0.0 ~ 1.0)
        generator_func: 지형 생성 함수
        
    Returns:
        (elevation, metadata) 튜플
    """
    cache_key = f"landform_{landform_name}_{grid_size}_{stage:.2f}"
    
    if cache_key not in st.session_state:
        try:
            result = generator_func(grid_size, stage, return_metadata=True)
            if isinstance(result, tuple):
                elevation, metadata = result[0], result[1] if len(result) > 1 else {}
            else:
                elevation, metadata = result, {}
        except TypeError:
            # return_metadata 미지원 함수
            elevation = generator_func(grid_size, stage)
            metadata = {}
        
        st.session_state[cache_key] = (elevation, metadata)
    
    return st.session_state[cache_key]


def cache_animation_frames(landform_name: str, grid_size: int, num_frames: int,
                           generator_func: Callable) -> list:
    """애니메이션 프레임 캐싱
    
    Args:
        landform_name: 지형 이름
        grid_size: 그리드 크기
        num_frames: 프레임 수
        generator_func: 지형 생성 함수
        
    Returns:
        [(elevation, metadata), ...] 리스트
    """
    cache_key = f"frames_{landform_name}_{grid_size}_{num_frames}"
    
    if cache_key not in st.session_state:
        frames = []
        for i in range(num_frames):
            stage = i / (num_frames - 1) if num_frames > 1 else 1.0
            try:
                result = generator_func(grid_size, stage, return_metadata=True)
                if isinstance(result, tuple):
                    elevation = result[0]
                    metadata = result[1] if len(result) > 1 else {}
                else:
                    elevation = result
                    metadata = {}
            except TypeError:
                elevation = generator_func(grid_size, stage)
                metadata = {}
            
            frames.append((elevation, metadata))
        
        st.session_state[cache_key] = frames
    
    return st.session_state[cache_key]


def clear_landform_cache():
    """지형 관련 캐시 모두 삭제"""
    keys_to_delete = [k for k in st.session_state.keys() 
                      if k.startswith('landform_') or k.startswith('frames_')]
    for key in keys_to_delete:
        del st.session_state[key]


def get_cache_stats() -> dict:
    """캐시 통계 반환"""
    landform_keys = [k for k in st.session_state.keys() if k.startswith('landform_')]
    frame_keys = [k for k in st.session_state.keys() if k.startswith('frames_')]
    
    return {
        'landform_count': len(landform_keys),
        'animation_count': len(frame_keys),
        'total_cached': len(landform_keys) + len(frame_keys)
    }
