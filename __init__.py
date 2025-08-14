"""
structured_output_benchmark 패키지 루트.

이 디렉토리(리포 루트) 자체가 패키지 최상위입니다.
"""

from importlib.metadata import version, PackageNotFoundError

try:  # 런타임 버전 노출
    __version__ = version("structured-output-benchmark")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "__version__",
]
