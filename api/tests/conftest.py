import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(API_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))