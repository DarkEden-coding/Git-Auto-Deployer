import os
import getpass
import subprocess


def get_uv_path() -> str:
    """Finds the absolute path to the uv executable.

    Returns:
        The absolute path to uv, or 'uv' if not found.
    """
    try:
        result = subprocess.run(
            ["which", "uv"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "uv"


def create_service_files() -> None:
    """Generates a systemd service file for the Git Auto Deployer.

    This function creates a git-auto-deploy.service file in the current directory.
    The service is configured to run the auto_deploy.py script continuously.
    """
    working_directory: str = os.path.abspath(os.getcwd())
    current_user: str = getpass.getuser()
    python_script: str = os.path.join(working_directory, "auto_deploy.py")
    uv_path: str = get_uv_path()

    service_content: str = f"""[Unit]
Description=Git Auto Deployer Service
After=network.target

[Service]
Type=simple
User={current_user}
WorkingDirectory={working_directory}
ExecStart={uv_path} run python {python_script}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    service_file_path: str = "git-auto-deploy.service"

    with open(service_file_path, "w") as service_file:
        service_file.write(service_content)

    print(f"Created {service_file_path}")

    # Installation
    try:
        dest_path: str = os.path.join("/etc/systemd/system/", service_file_path)
        print(f"Installing service to {dest_path}...")

        # Copy file
        subprocess.run(["sudo", "cp", service_file_path, dest_path], check=True)

        # Reload daemon
        print("Reloading systemd daemon...")
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)

        # Enable and start
        print("Enabling and starting git-auto-deploy.service...")
        subprocess.run(
            ["sudo", "systemctl", "enable", "--now", "git-auto-deploy.service"],
            check=True,
        )

        print("\n✅ Service installed and started successfully!")
    except subprocess.CalledProcessError as error:
        print(f"\n❌ Failed to install service: {error}")
        print("Please ensure you have sudo privileges.")


if __name__ == "__main__":
    create_service_files()
