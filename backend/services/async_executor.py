# backend/services/async_executor.py
# Lightweight async thread executor for non-blocking Flask operations

import asyncio
from concurrent.futures import ThreadPoolExecutor

# Shared thread pool (can be tuned if you expect heavy optimization loads)
_executor = ThreadPoolExecutor(max_workers=6)

async def run_in_threadpool(func, *args, **kwargs):
    """
    Run a blocking function in the thread pool without blocking Flask's async loop.
    Example:
        result = await run_in_threadpool(optimizer.calculate_optimal_speed_profile, vessel, weather)
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))
