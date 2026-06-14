# Copyright 2026 dynamaxx

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DYCORE_SOURCE = PROJECT_ROOT / "src" / "dynamaxx" / "dycore"
UTILS_SOURCE = PROJECT_ROOT / "src" / "dynamaxx" / "utils"
STABLE_SOURCE_DIRECTORIES = (
    PROJECT_ROOT / "src" / "dynamaxx" / "data",
    PROJECT_ROOT / "src" / "dynamaxx" / "eval",
)


def test_shared_dycore_layer_contains_only_shared_modules():
    """Keep shared dycore modules focused on API and reusable numerics."""
    root_modules = {path.name for path in DYCORE_SOURCE.glob("*.py")}

    assert root_modules == {
        "__init__.py",
        "api.py",
        "ode.py",
        "registry.py",
        "transport.py",
    }


def test_shared_utils_layer_contains_only_shared_modules():
    """Keep shared utility modules small and general."""
    root_modules = {path.name for path in UTILS_SOURCE.glob("*.py")}
    root_directories = {
        path.name
        for path in UTILS_SOURCE.iterdir()
        if path.is_dir() and path.name != "__pycache__"
    }

    assert root_modules == {"__init__.py", "consts.py"}
    assert root_directories == set()


def test_shared_dycore_implementation_is_not_model_specific():
    """Keep individual model names out of shared dycore implementation files."""
    model_specific_terms = set()
    for path in (DYCORE_SOURCE / "models").iterdir():
        if path.name == "__pycache__":
            continue
        if path.is_dir():
            model_specific_terms.add(path.name)
        elif path.suffix == ".py" and path.stem != "__init__":
            model_specific_terms.add(path.stem)

    for path in (
        DYCORE_SOURCE / "api.py",
        DYCORE_SOURCE / "ode.py",
        DYCORE_SOURCE / "transport.py",
    ):
        text = path.read_text(encoding="utf-8").lower()
        for term in model_specific_terms:
            assert term not in text, f"{path} contains model-specific term {term}"


def test_dycore_does_not_import_eval_or_data():
    """Keep dycore independent from evaluation and data-loading layers."""
    for path in DYCORE_SOURCE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        forbidden_imports = ("dynamaxx.eval", "dynamaxx.data")
        for forbidden_import in forbidden_imports:
            assert forbidden_import not in text, f"{path} imports {forbidden_import}"


def test_dycore_contains_no_target_fitting_hooks():
    """Prevent dycore implementations from fitting against evaluation targets."""
    forbidden_terms = (
        ".fit(",
        ".train(",
        "adam",
        "argmax",
        "argmin",
        "backprop",
        "bayesian",
        "calibrat",
        "curve_fit",
        "flax",
        "gradient_descent",
        "grid_search",
        "hyperparameter",
        "jax.grad",
        "jaxopt",
        "least_squares",
        "l-bfgs",
        "lbfgs",
        "loss",
        "lstsq",
        "minimize(",
        "optax",
        "optimizer",
        "polyfit",
        "primary_score",
        "protocol_score",
        "random_search",
        "regress",
        "scipy.optimize",
        "sklearn",
        "sgd",
        "tensorflow",
        "torch",
        "training",
        "train_step",
        "training_step",
        "value_and_grad",
    )
    for path in DYCORE_SOURCE.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for forbidden_term in forbidden_terms:
            assert forbidden_term not in text, f"{path} contains {forbidden_term}"


def test_stable_layers_do_not_import_model_implementations():
    """Keep stable data and eval layers independent from concrete model files."""
    for source_directory in STABLE_SOURCE_DIRECTORIES:
        for path in source_directory.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "dynamaxx.dycore.models" not in text, (
                f"{path} imports a dycore model implementation"
            )
