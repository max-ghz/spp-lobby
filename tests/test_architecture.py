"""
Guards the feature-based structure documented in ARCHITECTURE.md. Uses plain
ast parsing instead of a dependency, these checks are simple enough not to need one
"""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEATURES_DIR = ROOT / "features"
SHARED_DIR = ROOT / "shared"
APP_DIR = ROOT / "app"


def _python_files(directory: Path) -> list[Path]:
    return [p for p in directory.rglob("*.py") if "__pycache__" not in p.parts]


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def _feature_names() -> list[str]:
    return [p.name for p in FEATURES_DIR.iterdir() if p.is_dir() and p.name != "__pycache__"]


def test_main_has_no_business_logic():
    main_py = APP_DIR / "main.py"
    for module in _imported_modules(main_py):
        assert ".controllers" not in module, f"app/main.py imports {module}: controllers hold business logic"
        assert ".models" not in module, f"app/main.py imports {module}: models hold domain data"

    source = main_py.read_text()
    assert "try:" not in source, "app/main.py contains error handling, that belongs in a feature's controller"
    assert "json.loads" not in source, "app/main.py parses request data itself, that belongs in a controller"


def test_no_feature_imports_another_features_internals():
    for feature in _feature_names():
        for path in _python_files(FEATURES_DIR / feature):
            for module in _imported_modules(path):
                if not module.startswith("features."):
                    continue
                parts = module.split(".")
                imported_feature = parts[1]
                if imported_feature == feature:
                    continue
                assert len(parts) <= 2, (
                    f"{path.relative_to(ROOT)} imports {module}: a feature may only import "
                    f"another feature's public interface (features.{imported_feature}), not its internals"
                )


def _feature_dependency_graph() -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {feature: set() for feature in _feature_names()}
    for feature in graph:
        for path in _python_files(FEATURES_DIR / feature):
            for module in _imported_modules(path):
                if not module.startswith("features."):
                    continue
                imported_feature = module.split(".")[1]
                if imported_feature != feature:
                    graph[feature].add(imported_feature)
    return graph


def _has_cycle(graph: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(neighbor) for neighbor in graph.get(node, ())):
            return True
        visiting.discard(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def test_no_circular_dependencies_between_features():
    graph = _feature_dependency_graph()
    assert not _has_cycle(graph), f"circular dependency detected between features: {graph}"


def test_shared_does_not_import_features():
    for path in _python_files(SHARED_DIR):
        for module in _imported_modules(path):
            assert not module.startswith("features"), (
                f"{path.relative_to(ROOT)} imports {module}: shared/ must never depend on a feature"
            )


def test_routes_contain_no_business_logic():
    for feature in _feature_names():
        routes_file = FEATURES_DIR / feature / "routes.py"
        if not routes_file.exists():
            continue
        source = routes_file.read_text()
        for keyword in ("if ", "try:", "for ", "while "):
            assert keyword not in source, (
                f"{routes_file.relative_to(ROOT)} contains {keyword!r}: "
                "control flow belongs in controllers/, not routes.py"
            )


def test_no_stray_top_level_modules():
    root_python_files = {p.name for p in ROOT.glob("*.py")}
    assert not root_python_files, (
        f"unexpected top-level module(s) {root_python_files}: "
        "business logic must live under features/, not loose at the repo root"
    )

    allowed_app_modules = {"__init__.py", "__main__.py", "main.py"}
    app_python_files = {p.name for p in APP_DIR.glob("*.py")}
    assert app_python_files <= allowed_app_modules, (
        f"unexpected module(s) in app/: {app_python_files - allowed_app_modules}: "
        "app/ is just the entrypoint and composition root, feature code belongs under features/"
    )
