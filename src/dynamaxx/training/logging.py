# Copyright 2026 dynamaxx

"""Metrics-only Weights & Biases logging."""

from pathlib import Path
from typing import Any


class WandbMetricsLogger:
    """Log scalar training statistics without uploading any artifacts or files."""

    def __init__(
        self,
        *,
        project: str | None,
        run_name: str | None,
        local_directory: Path,
        run_id: str | None = None,
        resume: bool = False,
        enabled: bool = True,
    ):
        self._run: Any | None = None
        if not enabled:
            return
        import wandb

        settings = wandb.Settings(
            console="off",
            disable_code=True,
            disable_git=True,
            disable_job_creation=True,
            save_code=False,
            x_disable_meta=True,
            x_disable_stats=True,
            x_save_requirements=False,
        )
        self._run = wandb.init(
            project=project,
            name=run_name,
            dir=str(Path(local_directory).expanduser().resolve()),
            id=run_id,
            resume="must" if resume and run_id is not None else None,
            config=None,
            save_code=False,
            settings=settings,
        )

    @property
    def run_id(self) -> str | None:
        """W&B run identifier without exposing the run object."""
        return None if self._run is None else str(self._run.id)

    def log(self, metrics: dict[str, float], *, step: int) -> None:
        """Log scalar statistics at one optimizer step."""
        if self._run is None:
            return
        scalar_metrics = {str(name): float(value) for name, value in metrics.items()}
        self._run.log(scalar_metrics, step=int(step))

    def finish(self) -> None:
        """Flush scalar history and close the run."""
        if self._run is not None:
            self._run.finish()
            self._run = None

    def __enter__(self) -> "WandbMetricsLogger":
        return self

    def __exit__(self, exception_type, exception, traceback) -> None:
        del exception_type, exception, traceback
        self.finish()
