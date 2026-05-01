"""
WSGI entry point for Vercel serverless deployment
"""
import os
import sys

# Ensure the current directory is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Vercel environment variable for Flask
os.environ['VERCEL'] = '1'

from app import app

# Export for Vercel
__all__ = ['app']
