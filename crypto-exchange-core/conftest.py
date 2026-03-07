"""Pytest configuration and fixtures."""
import sys
import os

# Add the project root to sys.path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
