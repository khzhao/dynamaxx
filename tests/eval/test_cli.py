import pytest

from dynamaxx.eval import cli
from dynamaxx.utils.consts import WEATHERBENCH2_ERA5_1P5DEG_6H_PATH


def test_eval_cli_dispatches_smoke_protocol(monkeypatch):
    call = {}

    def run_smoke(*, dataset, output_dir, model_name):
        call["dataset"] = dataset
        call["output_dir"] = output_dir
        call["model_name"] = model_name
        return 0

    monkeypatch.setattr(cli, "run_smoke", run_smoke)

    exit_code = cli.main(
        [
            "smoke",
            "--dataset",
            "memory://weatherbench2",
            "--output-dir",
            "memory://metrics",
            "--model",
            "custom_model",
        ]
    )

    assert exit_code == 0
    assert call == {
        "dataset": "memory://weatherbench2",
        "output_dir": "memory://metrics",
        "model_name": "custom_model",
    }


def test_eval_cli_uses_fixed_default_dataset(monkeypatch):
    call = {}

    def run_fast(*, dataset, output_dir, model_name):
        call["dataset"] = dataset
        call["output_dir"] = output_dir
        call["model_name"] = model_name
        return 0

    monkeypatch.setattr(cli, "run_fast", run_fast)

    assert cli.main(["fast"]) == 0
    assert call == {
        "dataset": WEATHERBENCH2_ERA5_1P5DEG_6H_PATH,
        "output_dir": "outputs/eval",
        "model_name": "spectral_dycore",
    }


def test_eval_cli_dispatches_candidate_year(monkeypatch):
    call = {}

    def run_candidate_year(year, *, dataset, output_dir, model_name):
        call["year"] = year
        call["dataset"] = dataset
        call["output_dir"] = output_dir
        call["model_name"] = model_name
        return 0

    monkeypatch.setattr(cli, "run_candidate_year", run_candidate_year)

    assert cli.main(["candidate-year", "2019"]) == 0
    assert call == {
        "year": 2019,
        "dataset": WEATHERBENCH2_ERA5_1P5DEG_6H_PATH,
        "output_dir": "outputs/eval",
        "model_name": "spectral_dycore",
    }


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
    assert "protocols" in output
    assert "smoke" in output
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
