#!/usr/bin/env python3
"""
Entry point for the news ingestion pipeline.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main pipeline
from src.main import main

if __name__ == '__main__':
    main()