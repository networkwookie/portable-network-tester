"""
Pytest configuration file.
"""
import sys
from pathlib import Path

# Add src directory to Python path - use absolute path and insert at position 0
src_path = (Path(__file__).parent / "src").absolute()
sys.path.insert(0, str(src_path))
