from pathlib import Path

import pytest

from dynamaxx import cli


def test_eval_cli_dispatches_fixed_protocol(monkeypatch):
    call = {}

    def run_protocol(
        protocol,
        *,
        model_name,
        hybrid_checkpoint=None,
        use_hybrid_ema=True,
        worker_count=1,
        resume=True,
        output_directory=cli.OUTPUT_DIR,
    ):
        call["protocol"] = protocol
        call["model_name"] = model_name
        call["hybrid_checkpoint"] = hybrid_checkpoint
        call["use_hybrid_ema"] = use_hybrid_ema
        call["worker_count"] = worker_count
        call["resume"] = resume
        call["output_directory"] = output_directory
        return 0

    monkeypatch.setattr(cli, "run_protocol", run_protocol)

    exit_code = cli.main(
        ["validation", "--model", "custom_model", "--workers", "3", "--restart"]
    )

    assert exit_code == 0
    assert call == {
        "protocol": "validation",
        "model_name": "custom_model",
        "hybrid_checkpoint": None,
        "use_hybrid_ema": True,
        "worker_count": 3,
        "resume": False,
        "output_directory": cli.OUTPUT_DIR,
    }


def test_eval_cli_uses_default_model(monkeypatch):
    call = {}

    def run_protocol(
        protocol,
        *,
        model_name,
        hybrid_checkpoint=None,
        use_hybrid_ema=True,
        worker_count=1,
        resume=True,
        output_directory=cli.OUTPUT_DIR,
    ):
        call["protocol"] = protocol
        call["model_name"] = model_name
        call["hybrid_checkpoint"] = hybrid_checkpoint
        call["use_hybrid_ema"] = use_hybrid_ema
        call["worker_count"] = worker_count
        call["resume"] = resume
        call["output_directory"] = output_directory
        return 0

    monkeypatch.setattr(cli, "run_protocol", run_protocol)

    assert cli.main(["fast"]) == 0
    assert call == {
        "protocol": "fast",
        "model_name": "persistence",
        "hybrid_checkpoint": None,
        "use_hybrid_ema": True,
        "worker_count": 1,
        "resume": True,
        "output_directory": cli.OUTPUT_DIR,
    }


def test_eval_cli_dispatches_hybrid_checkpoint(monkeypatch, tmp_path):
    call = {}

    def run_protocol(protocol, **kwargs):
        call["protocol"] = protocol
        call.update(kwargs)
        return 0

    monkeypatch.setattr(cli, "run_protocol", run_protocol)
    checkpoint = tmp_path / "step.pkl"
    output_directory = tmp_path / "metrics"

    assert (
        cli.main(
            [
                "weatherbench2",
                "--hybrid-checkpoint",
                str(checkpoint),
                "--raw-hybrid-parameters",
                "--workers",
                "8",
                "--output-directory",
                str(output_directory),
            ]
        )
        == 0
    )
    assert call == {
        "protocol": "weatherbench2",
        "model_name": "persistence",
        "hybrid_checkpoint": Path(checkpoint),
        "use_hybrid_ema": False,
        "worker_count": 8,
        "resume": True,
        "output_directory": Path(output_directory),
    }


def test_eval_cli_rejects_removed_smoke_protocol():
    with pytest.raises(SystemExit) as error:
        cli.main(["smoke"])

    assert error.value.code == 2


def test_eval_cli_without_arguments_prints_usage(capsys):
    with pytest.raises(SystemExit) as error:
        cli.main([])

    assert error.value.code == 2
    assert "usage: dynamaxx-eval" in capsys.readouterr().err


def test_eval_cli_help_is_small_and_fast(capsys):
    with pytest.raises(SystemExit) as error:
        cli.main(["--help"])

    assert error.value.code == 0
    output = capsys.readouterr().out
    assert "fast" in output
    assert "iteration" in output
    assert "validation" in output
    assert "golden" in output
    assert "--workers" in output
    assert "--restart" in output
    assert "train" not in output
    assert "test" not in output
    assert "smoke" not in output
    assert "--dataset" not in output
    assert "grid" not in output


def test_eval_cli_help_does_not_import_jax(capsys):
    import sys

    sys.modules.pop("jax", None)
    sys.modules.pop("jax.numpy", None)

    with pytest.raises(SystemExit) as error:
        cli.main(["--help"])

    assert error.value.code == 0
    assert "jax" not in sys.modules


def test_eval_cli_configures_package_logging_only():
    cli._configure_logging()

    assert cli.logging.getLogger("dynamaxx").level == cli.logging.INFO
    assert not cli.logging.getLogger("dynamaxx").propagate
