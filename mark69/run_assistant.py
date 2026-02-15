#!/usr/bin/env python3
"""Run the offline multimodal AI assistant from project root."""
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from assistant.main import main

if __name__ == "__main__":
    main()
