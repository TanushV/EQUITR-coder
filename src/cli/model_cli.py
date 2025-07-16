import argparse
import sys
from typing import List
from src.config.model_config import get_config_manager


class ModelCLI:
    def __init__(self):
        self.config_manager = get_config_manager()

    def create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Model configuration CLI")
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Set mode command
        mode_parser = subparsers.add_parser(
            "mode", help="Set model mode (single/multi)"
        )
        mode_parser.add_argument("mode", choices=["single", "multi"], help="Model mode")

        # Set models command
        models_parser = subparsers.add_parser("models", help="Set active models")
        models_parser.add_argument("primary", help="Primary model")
        models_parser.add_argument(
            "--secondary", help="Secondary model (for multi-mode)"
        )

        # Show current config
        show_parser = subparsers.add_parser("show", help="Show current configuration")

        # List available models
        list_parser = subparsers.add_parser("list", help="List available models")

        # Reset to defaults
        reset_parser = subparsers.add_parser(
            "reset", help="Reset to default configuration"
        )

        return parser

    def run(self, args: List[str] = None):
        if args is None:
            args = sys.argv[1:]

        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        if parsed_args.command == "mode":
            self.set_mode(parsed_args.mode)
        elif parsed_args.command == "models":
            self.set_models(parsed_args.primary, parsed_args.secondary)
        elif parsed_args.command == "show":
            self.show_config()
        elif parsed_args.command == "list":
            self.list_models()
        elif parsed_args.command == "reset":
            self.reset_config()
        else:
            parser.print_help()

    def set_mode(self, mode: str):
        try:
            self.config_manager.set_mode(mode)
            print(f"Model mode set to: {mode}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def set_models(self, primary: str, secondary: str = None):
        available = self.config_manager.get_available_models()

        if primary not in available:
            print(f"Error: Primary model '{primary}' not available", file=sys.stderr)
            print(f"Available models: {', '.join(available)}", file=sys.stderr)
            sys.exit(1)

        if secondary and secondary not in available:
            print(
                f"Error: Secondary model '{secondary}' not available", file=sys.stderr
            )
            print(f"Available models: {', '.join(available)}", file=sys.stderr)
            sys.exit(1)

        self.config_manager.set_models(primary, secondary)
        print(f"Models configured: primary={primary}", end="")
        if secondary:
            print(f", secondary={secondary}")
        else:
            print()

    def show_config(self):
        config = self.config_manager.get_config()
        print("Current Model Configuration:")
        print(f"  Mode: {config.mode}")
        print(f"  Primary Model: {config.primary_model}")
        if config.secondary_model:
            print(f"  Secondary Model: {config.secondary_model}")
        print(f"  Active Models: {', '.join(config.models)}")

    def list_models(self):
        available = self.config_manager.get_available_models()
        print("Available Models:")
        for model in available:
            print(f"  - {model}")

    def reset_config(self):
        from src.config.model_config import ModelConfig

        self.config_manager.save_config(ModelConfig())
        print("Configuration reset to defaults")


def main():
    cli = ModelCLI()
    cli.run()


if __name__ == "__main__":
    main()
