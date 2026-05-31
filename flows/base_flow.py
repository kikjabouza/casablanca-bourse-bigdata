# flows/base_flow.py
from datetime import timedelta
from typing import Any, Callable, Optional

from prefect import flow, get_run_logger, task
from prefect.tasks import task_input_hash

from src.utils.logger import setup_logger


class BaseFlow:
    """Classe de base pour tous les flows Prefect du projet."""

    DEFAULT_RETRIES = 3
    DEFAULT_RETRY_DELAY = timedelta(seconds=30)

    def __init__(self, flow_name: str):
        self.flow_name = flow_name
        setup_logger()

    @staticmethod
    def build_task(
        name: str,
        retries: int = 3,
        retry_delay_seconds: int = 30,
        cache_expiration: Optional[timedelta] = None,
    ):
        task_kwargs = {
            "name": name,
            "retries": retries,
            "retry_delay_seconds": retry_delay_seconds,
            "log_prints": True,
        }
        if cache_expiration is not None:
            task_kwargs["cache_key_fn"] = task_input_hash
            task_kwargs["cache_expiration"] = cache_expiration
        return task(**task_kwargs)

    def run_task(self, task_fn: Callable, *args, **kwargs) -> Any:
        logger = get_run_logger()
        try:
            logger.info(f"Exécution tâche {task_fn.name}")
            return task_fn(*args, **kwargs)
        except Exception as exc:
            logger.error(f"Erreur tâche {task_fn.name}: {exc}")
            raise

    @staticmethod
    def create_flow(name: str, description: str = ""):
        return flow(name=name, description=description, log_prints=True)
