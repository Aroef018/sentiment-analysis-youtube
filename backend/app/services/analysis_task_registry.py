import asyncio
from typing import Dict

# Global registry for running analysis tasks per user
# user_id (UUID) -> asyncio.Task
running_analysis_tasks: Dict[str, asyncio.Task] = {}
