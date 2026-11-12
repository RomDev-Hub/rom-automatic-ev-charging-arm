"""On-device control core of the automatic EV charging arm."""


def __getattr__(name: str) -> str:
    # Read on access, so that importing the package stays free of side effects.
    if name == "__version__":
        from importlib.metadata import version

        return version("robot-core")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
