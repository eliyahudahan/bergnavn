# backend/services/async_executor.py
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=6)

async def run_in_threadpool(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Run blocking function asynchronously in a shared thread pool."""
    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))
        logger.debug(f"Executed {func.__name__} successfully")
        return result
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {e}")
        raise
