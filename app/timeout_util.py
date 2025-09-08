# app/timeout_util.py

import asyncio
import functools
from typing import Any, Callable, Optional


def with_timeout(seconds: int):
    """
    Decorator to add timeout to async functions.
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        Decorated function with timeout
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                # Log timeout error and return None or raise appropriate exception
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Function {func.__name__} timed out after {seconds} seconds")
                return None
        return wrapper
    return decorator
