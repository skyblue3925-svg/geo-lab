"""
DEM 입출력 유틸리티 (DEM I/O Utilities)

지원 포맷:
- CSV: 쉼표 구분 고도 데이터
- NumPy: .npy 바이너리 포맷
- GeoTIFF: 지리참조 래스터 (rasterio 필요)
- ASC: ESRI ASCII Grid 포맷
"""
import numpy as np
import json
import os
from datetime import datetime
from typing import Tuple, Dict, Optional, Any
from io import BytesIO, StringIO


def load_dem_csv(file_content: str, delimiter: str = ',') -> np.ndarray:
    """
    CSV 파일에서 DEM 불러오기
    
    Args:
        file_content: CSV 파일 내용 (문자열)
        delimiter: 구분자
    
    Returns:
        numpy.ndarray: 고도 배열
    """
    try:
        # StringIO로 파일처럼 읽기
        data = np.loadtxt(StringIO(file_content), delimiter=delimiter)
        return data.astype(np.float64)
    except Exception as e:
        raise ValueError(f"CSV 파싱 오류: {e}")


def load_dem_npy(file_bytes: bytes) -> np.ndarray:
    """NumPy 파일에서 DEM 불러오기"""
    try:
        return np.load(BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"NPY 파싱 오류: {e}")


def load_dem_asc(file_content: str) -> Tuple[np.ndarray, Dict]:
    """
    ESRI ASCII Grid (.asc) 파일에서 DEM 불러오기
    
    Returns:
        tuple: (고도 배열, 메타데이터)
    """
    lines = file_content.strip().split('\n')
    
    # 헤더 파싱 (첫 6줄)
    header = {}
    data_start = 0
    
    for i, line in enumerate(lines):
        parts = line.strip().split()
        if len(parts) == 2:
            key = parts[0].lower()
            try:
                value = float(parts[1])
                header[key] = value
                data_start = i + 1
            except ValueError:
                break
        else:
            break
    
    # 데이터 파싱
    data_lines = lines[data_start:]
    data = []
    for line in data_lines:
        row = [float(x) for x in line.strip().split()]
        if row:
            data.append(row)
    
    elevation = np.array(data)
    
    # NODATA 처리
    nodata = header.get('nodata_value', -9999)
    elevation[elevation == nodata] = np.nan
    
    metadata = {
        'ncols': int(header.get('ncols', elevation.shape[1])),
        'nrows': int(header.get('nrows', elevation.shape[0])),
        'xllcorner': header.get('xllcorner', 0),
        'yllcorner': header.get('yllcorner', 0),
        'cellsize': header.get('cellsize', 1.0),
        'nodata_value': nodata
    }
    
    return elevation, metadata


def save_dem_csv(elevation: np.ndarray, filepath: str, delimiter: str = ','):
    """DEM을 CSV로 저장"""
    np.savetxt(filepath, elevation, delimiter=delimiter, fmt='%.4f')


def save_dem_npy(elevation: np.ndarray, filepath: str):
    """DEM을 NumPy 포맷으로 저장"""
    np.save(filepath, elevation)


def save_dem_asc(
    elevation: np.ndarray,
    filepath: str,
    cellsize: float = 1.0,
    xllcorner: float = 0.0,
    yllcorner: float = 0.0,
    nodata: float = -9999
):
    """DEM을 ESRI ASCII Grid로 저장"""
    nrows, ncols = elevation.shape
    
    # NaN을 NODATA로 변환
    data = elevation.copy()
    data[np.isnan(data)] = nodata
    
    with open(filepath, 'w') as f:
        f.write(f"ncols {ncols}\n")
        f.write(f"nrows {nrows}\n")
        f.write(f"xllcorner {xllcorner}\n")
        f.write(f"yllcorner {yllcorner}\n")
        f.write(f"cellsize {cellsize}\n")
        f.write(f"nodata_value {nodata}\n")
        
        for row in data:
            f.write(' '.join(f'{x:.4f}' for x in row) + '\n')


def export_to_bytes_csv(elevation: np.ndarray) -> bytes:
    """DEM을 CSV 바이트로 변환 (다운로드용)"""
    output = BytesIO()
    np.savetxt(output, elevation, delimiter=',', fmt='%.4f')
    return output.getvalue()


def export_to_bytes_npy(elevation: np.ndarray) -> bytes:
    """DEM을 NumPy 바이트로 변환 (다운로드용)"""
    output = BytesIO()
    np.save(output, elevation)
    return output.getvalue()


def save_parameters_json(
    params: Dict[str, Any],
    filepath: str,
    include_timestamp: bool = True
):
    """
    파라미터를 JSON으로 저장 (재현성 확보)
    
    Args:
        params: 파라미터 딕셔너리
        filepath: 저장 경로
        include_timestamp: 타임스탬프 포함 여부
    """
    if include_timestamp:
        params['_timestamp'] = datetime.now().isoformat()
        params['_version'] = 'Geo-Lab v1.0'
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(params, f, indent=2, ensure_ascii=False)


def load_parameters_json(filepath: str) -> Dict[str, Any]:
    """JSON에서 파라미터 불러오기"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_export_bundle(
    elevation: np.ndarray,
    parameters: Dict[str, Any],
    output_dir: str,
    prefix: str = "geo_lab"
) -> Dict[str, str]:
    """
    고도 데이터 + 파라미터를 번들로 저장
    
    Returns:
        dict: 저장된 파일 경로들
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(output_dir, exist_ok=True)
    
    paths = {}
    
    # CSV 저장
    csv_path = os.path.join(output_dir, f"{prefix}_{timestamp}.csv")
    save_dem_csv(elevation, csv_path)
    paths['csv'] = csv_path
    
    # NumPy 저장
    npy_path = os.path.join(output_dir, f"{prefix}_{timestamp}.npy")
    save_dem_npy(elevation, npy_path)
    paths['npy'] = npy_path
    
    # ASC 저장
    asc_path = os.path.join(output_dir, f"{prefix}_{timestamp}.asc")
    cell_size = parameters.get('cell_size', 1.0)
    save_dem_asc(elevation, asc_path, cellsize=cell_size)
    paths['asc'] = asc_path
    
    # 파라미터 JSON 저장
    json_path = os.path.join(output_dir, f"{prefix}_{timestamp}_params.json")
    save_parameters_json(parameters, json_path)
    paths['params'] = json_path
    
    return paths


def get_dem_statistics(elevation: np.ndarray) -> Dict[str, float]:
    """DEM 기본 통계 계산"""
    valid = elevation[~np.isnan(elevation)]
    
    if len(valid) == 0:
        return {'error': 'No valid data'}
    
    return {
        'min': float(np.min(valid)),
        'max': float(np.max(valid)),
        'mean': float(np.mean(valid)),
        'std': float(np.std(valid)),
        'median': float(np.median(valid)),
        'range': float(np.max(valid) - np.min(valid)),
        'valid_cells': int(len(valid)),
        'total_cells': int(elevation.size),
        'nodata_cells': int(elevation.size - len(valid))
    }
