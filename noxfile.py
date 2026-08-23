from __future__ import annotations

import nox

nox.options.default_venv_backend = "none"


@nox.session(name="lint")
def lint(session: nox.Session) -> None:
    session.run("uv", "run", "ruff", "format", "--check", "src", "tests")
    session.run("uv", "run", "ruff", "check", "src", "tests")


@nox.session(name="typing")
def typing(session: nox.Session) -> None:
    session.run("uv", "run", "pyright")


@nox.session(name="dead-code")
def dead_code(session: nox.Session) -> None:
    session.run(
        "uv",
        "run",
        "vulture",
        "src",
        "tests",
        "--min-confidence",
        "80",
    )


@nox.session(name="dependency-hygiene")
def dependency_hygiene(session: nox.Session) -> None:
    session.run("uv", "run", "deptry", ".")


@nox.session(name="unit")
def unit(session: nox.Session) -> None:
    session.run("uv", "run", "pytest", "tests/unit", "tests/scientific")


@nox.session(name="architecture")
def architecture(session: nox.Session) -> None:
    session.run("uv", "run", "pytest", "tests/architecture")


@nox.session(name="checks")
def checks(session: nox.Session) -> None:
    session.notify("lint")
    session.notify("typing")
    session.notify("dead-code")
    session.notify("dependency-hygiene")
    session.notify("unit")
    session.notify("architecture")
