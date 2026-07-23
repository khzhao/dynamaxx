import sys
from types import SimpleNamespace

from dynamaxx.training.logging import WandbMetricsLogger


class _FakeRun:
    id = "run-123"

    def __init__(self):
        self.logged = []
        self.finished = False

    def log(self, metrics, *, step):
        self.logged.append((metrics, step))

    def finish(self):
        self.finished = True


def test_wandb_wrapper_sends_only_explicit_scalar_metrics(monkeypatch, tmp_path):
    fake_run = _FakeRun()
    calls = {}

    class FakeSettings:
        def __init__(self, **kwargs):
            calls["settings"] = kwargs

    def fake_init(**kwargs):
        calls["init"] = kwargs
        return fake_run

    monkeypatch.setitem(
        sys.modules,
        "wandb",
        SimpleNamespace(Settings=FakeSettings, init=fake_init),
    )

    logger = WandbMetricsLogger(
        project="project",
        run_name="run",
        local_directory=tmp_path,
    )
    logger.log({"loss": 1, "gradient_norm": 2.5}, step=4)
    logger.finish()

    assert calls["init"]["config"] is None
    assert calls["init"]["save_code"] is False
    assert calls["settings"]["x_disable_stats"] is True
    assert calls["settings"]["x_disable_meta"] is True
    assert fake_run.logged == [({"loss": 1.0, "gradient_norm": 2.5}, 4)]
    assert fake_run.finished
