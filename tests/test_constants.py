import pytest
from importlib import reload


# Test constants with environment variables set
@pytest.mark.parametrize(
    "env_var,expected_value,default_value",
    [
        ("ACTION_TYPE", "test-action", None),
        ("GITHUB_TOKEN", "test-token", None),
        ("OPENAI_API_KEY", "test-key", None),
        ("CUSTOM_PROMPT", "test-prompt", None),
        ("MODEL", "gpt-4", "gpt-4o-mini"),
        ("LOG_LEVEL", "debug", "INFO"),
        ("GITHUB_EVENT_PATH", "/path/to/event.json", None),
        ("MAX_TURNS", "50", "30"),
    ],
)
def test_constants_from_env(env_var, expected_value, default_value, monkeypatch):
    """Test that constants are correctly loaded from environment variables."""
    # Clear any existing env var
    monkeypatch.delenv(env_var, raising=False)
    # Set the test environment variable
    monkeypatch.setenv(env_var, expected_value)

    # Import and reload constants to pick up the new environment
    import src.constants

    reload(src.constants)

    # Get the constant value using getattr
    actual_value = getattr(src.constants, env_var)

    # For MAX_TURNS, we need to compare as integers
    if env_var == "MAX_TURNS":
        assert actual_value == int(expected_value)
    # For LOG_LEVEL, it's converted to uppercase in constants.py
    elif env_var == "LOG_LEVEL":
        assert actual_value == expected_value.upper()
    else:
        assert actual_value == expected_value


@pytest.mark.parametrize(
    "env_var,default_value",
    [
        ("MODEL", "gpt-4o-mini"),
        ("LOG_LEVEL", "INFO"),
        ("MAX_TURNS", 30),
    ],
)
def test_constants_defaults(env_var, default_value, monkeypatch):
    """Test that constants have correct default values when env vars are missing."""
    # Remove the environment variable if it exists
    monkeypatch.delenv(env_var, raising=False)

    # Import and reload constants with clean environment
    import src.constants

    reload(src.constants)

    # Get the constant value using getattr
    actual_value = getattr(src.constants, env_var)

    assert actual_value == default_value
