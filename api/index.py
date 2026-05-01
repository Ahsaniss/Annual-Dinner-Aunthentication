"""
Vercel serverless function entry point
"""
import os
import sys

# Ensure parent directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Vercel environment before importing app
os.environ['VERCEL'] = '1'

from app import app

# This is the WSGI application that Vercel will call
handler = app
