import pytest

from dynamaxx import cli


def test_eval_cli_dispatches_fixed_protocol(monkeypatch):
    call = {}

    def run_protocol(protocol, *, model_name):
        call["protocol"] = protocol
        call["model_name"] = model_name
        return 0

    monkeypatch.setattr(cli, "run_protocol", run_protocol)

    exit_code = cli.main(["validation", "--model", "custom_model"])

    assert exit_code == 0
    assert call == {
        "protocol": "validation",
        "model_name": "custom_model",
    }


def test_eval_cli_uses_default_model(monkeypatch):
    call = {}

    def run_protocol(protocol, *, model_name):
        call["protocol"] = protocol
        call["model_name"] = model_name
        return 0

    monkeypatch.setattr(cli, "run_protocol", run_protocol)

    assert cli.main(["fast"]) == 0
    assert call == {
        "protocol": "fast",
        "model_name": "persistence",
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
    assert "validation" in output
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
