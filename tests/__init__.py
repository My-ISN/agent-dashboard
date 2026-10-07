"""
ISKOM AI-OS Test Suite Package
"""
import sys
import os

# Otomatis daftarkan root project ke sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
