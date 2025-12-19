#!/usr/bin/env python3
import json
import os
from typing import Dict


def create_config() -> None:
    """Prompts the user for configuration values and saves them to config.json."""
    config_data: Dict[str, str] = {
        "REPO": input("Enter the GitHub repository (owner/repo): ") or "owner/repo",
        "SERVICE_NAME": input("Enter the systemd service name: ")
        or "your-service.service",
        "TARGET_DIR": input("Enter the target directory for deployment: ")
        or "/path/to/app",
        "STATE_FILE": input("Enter the path for the state file: ")
        or "/var/lib/app_updater_version.txt",
        "MAINTENANCE_PORT": input("Enter the maintenance server port (default 8080): ")
        or "8080",
    }

    config_path: str = os.path.join(os.getcwd(), "config.json")
    with open(config_path, "w") as config_file:
        json.dump(config_data, config_file, indent=4)

    print(f"Configuration saved to {config_path}")


if __name__ == "__main__":
    create_config()
