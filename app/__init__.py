#!/usr/bin/env python

"""
Database initialization script for Residere Assistant
Run this to create all tables in your database if they don't exist.

Usage:
    python init_db.py
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Import database models and init function
    from app.models import init_db

    # Initialize database
    logger.info("Initializing database tables...")
    init_db()
    logger.info("Database initialization complete!")

except Exception as e:
    logger.warning(f"Database initialization failed (will retry on first request): {e}")
    # Don't exit - let the app start and retry database connection on first request