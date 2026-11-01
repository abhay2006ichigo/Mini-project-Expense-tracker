"""
Vercel Serverless Function entrypoint.
Proxies directly to the top-level Flask app instance.
"""
import os
import sys

# Ensure project root is accessible on sys.path in serverless environment
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app, application

__all__ = ["app", "application"]
