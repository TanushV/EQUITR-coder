"""Environment variable loader with .env file support."""

import os
from pathlib import Path
from typing import Optional, Dict, Any


def load_dotenv_file(env_file: Optional[str] = None) -> bool:
    """
    Load environment variables from a .env file.

    Args:
        env_file: Path to .env file. If None, searches for .env in current directory and parents.

    Returns:
        bool: True if .env file was found and loaded successfully
    """
    try:
        from dotenv import load_dotenv

        if env_file:
            # Use specific file
            env_path = Path(env_file)
            if env_path.exists():
                load_dotenv(
                    env_path, override=False
                )  # Don't override existing env vars
                print(f"✅ Loaded environment variables from {env_path}")
                return True
            else:
                print(f"⚠️  .env file not found at {env_path}")
                return False
        else:
            # Search for .env file in current directory and parents
            current_dir = Path.cwd()
            for parent in [current_dir] + list(current_dir.parents):
                env_path = parent / ".env"
                if env_path.exists():
                    load_dotenv(
                        env_path, override=False
                    )  # Don't override existing env vars
                    print(f"✅ Loaded environment variables from {env_path}")
                    return True

            print("⚠️  No .env file found in current directory or parents")
            return False

    except ImportError:
        print(
            "⚠️  python-dotenv not installed. Install with: pip install python-dotenv"
        )
        return False
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False


def get_api_key(provider: str, env_var: Optional[str] = None) -> Optional[str]:
    """
    Get API key for a specific provider from environment variables.

    Args:
        provider: Provider name (openai, moonshot, openrouter, anthropic, etc.)
        env_var: Specific environment variable name to check

    Returns:
        API key if found, None otherwise
    """
    # Try specific env_var first
    if env_var and env_var in os.environ:
        return os.environ[env_var]

    # Standard environment variable names for common providers
    provider_env_vars = {
        "openai": ["OPENAI_API_KEY", "OPENAI_API_TOKEN"],
        "moonshot": ["MOONSHOT_API_KEY", "MOONSHOT_API_TOKEN"],
        "openrouter": ["OPENROUTER_API_KEY", "OPENROUTER_API_TOKEN"],
        "anthropic": ["ANTHROPIC_API_KEY", "ANTHROPIC_API_TOKEN"],
        "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "cohere": ["COHERE_API_KEY"],
        "replicate": ["REPLICATE_API_TOKEN"],
        "huggingface": ["HUGGINGFACE_API_KEY", "HF_TOKEN"],
    }

    # Check provider-specific environment variables
    provider_lower = provider.lower()
    if provider_lower in provider_env_vars:
        for env_var_name in provider_env_vars[provider_lower]:
            if env_var_name in os.environ:
                return os.environ[env_var_name]

    # Check generic API_KEY
    if "API_KEY" in os.environ:
        return os.environ["API_KEY"]

    return None


def setup_provider_environment(provider: str, api_key: Optional[str] = None) -> bool:
    """
    Set up environment variables for a specific provider.

    Args:
        provider: Provider name
        api_key: API key to set (if None, tries to find from existing env vars)

    Returns:
        bool: True if API key was set successfully
    """
    if not api_key:
        api_key = get_api_key(provider)

    if not api_key:
        return False

    # Set provider-specific environment variables
    provider_lower = provider.lower()

    if provider_lower == "openai":
        os.environ["OPENAI_API_KEY"] = api_key
    elif provider_lower == "moonshot":
        os.environ["MOONSHOT_API_KEY"] = api_key
        # Set the correct API base URL for Moonshot AI (OpenAI-compatible)
        if "MOONSHOT_API_BASE" not in os.environ:
            os.environ["MOONSHOT_API_BASE"] = "https://api.moonshot.ai/v1"
    elif provider_lower == "openrouter":
        os.environ["OPENROUTER_API_KEY"] = api_key
    elif provider_lower == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = api_key
    elif provider_lower == "google":
        os.environ["GOOGLE_API_KEY"] = api_key
    elif provider_lower == "cohere":
        os.environ["COHERE_API_KEY"] = api_key
    else:
        # Generic fallback
        os.environ["API_KEY"] = api_key

    return True


def get_available_providers() -> Dict[str, Any]:
    """
    Check which providers have API keys available in environment.

    Returns:
        Dict mapping provider names to their status and API key info
    """
    providers = {}

    provider_checks = [
        ("openai", ["OPENAI_API_KEY"]),
        ("moonshot", ["MOONSHOT_API_KEY"]),
        ("openrouter", ["OPENROUTER_API_KEY"]),
        ("anthropic", ["ANTHROPIC_API_KEY"]),
        ("google", ["GOOGLE_API_KEY", "GEMINI_API_KEY"]),
        ("cohere", ["COHERE_API_KEY"]),
        ("replicate", ["REPLICATE_API_TOKEN"]),
        ("huggingface", ["HUGGINGFACE_API_KEY", "HF_TOKEN"]),
    ]

    for provider, env_vars in provider_checks:
        api_key = None
        env_var_found = None

        for env_var in env_vars:
            if env_var in os.environ and os.environ[env_var]:
                api_key = os.environ[env_var]
                env_var_found = env_var
                break

        providers[provider] = {
            "available": api_key is not None,
            "env_var": env_var_found,
            "key_length": len(api_key) if api_key else 0,
            "key_preview": f"{api_key[:8]}...{api_key[-4:]}"
            if api_key and len(api_key) > 12
            else None,
        }

    return providers


def auto_load_environment() -> Dict[str, Any]:
    """
    Automatically load environment variables and return provider status.

    Returns:
        Dict with loading status and available providers
    """
    # Try to load .env file
    dotenv_loaded = load_dotenv_file()

    # Check available providers
    providers = get_available_providers()
    available_count = sum(1 for p in providers.values() if p["available"])

    return {
        "dotenv_loaded": dotenv_loaded,
        "providers": providers,
        "available_providers": available_count,
        "total_providers": len(providers),
    }


if __name__ == "__main__":
    """Test the environment loader."""
    print("🔧 Environment Variable Loader Test")
    print("=" * 40)

    status = auto_load_environment()

    print(f"📁 .env file loaded: {'✅' if status['dotenv_loaded'] else '❌'}")
    print(
        f"🔑 Available providers: {status['available_providers']}/{status['total_providers']}"
    )
    print()

    print("📋 Provider Status:")
    for provider, info in status["providers"].items():
        status_icon = "✅" if info["available"] else "❌"
        if info["available"]:
            print(
                f"  {status_icon} {provider}: {info['env_var']} ({info['key_length']} chars)"
            )
        else:
            print(f"  {status_icon} {provider}: No API key found")
