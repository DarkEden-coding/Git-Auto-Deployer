import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional, Dict, List


class CustomHTTPServer(ThreadingHTTPServer):
    """Custom ThreadingHTTPServer with additional attributes."""

    address_family = socket.AF_INET6 if socket.has_ipv6 else socket.AF_INET
    allow_reuse_address = True
    public_dir: str
    current_status: Dict


class StatusHandler(BaseHTTPRequestHandler):
    """Handles static files and status polling."""

    server: CustomHTTPServer

    def log_message(self, format: str, *args) -> None:
        """Log requests to stdout instead of stderr."""
        sys.stdout.write(
            "%s - - [%s] %s\n"
            % (self.address_string(), self.log_date_time_string(), format % args)
        )

    def do_GET(self) -> None:
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()

            if hasattr(self.server, "current_status"):
                data = json.dumps(self.server.current_status)
                self.wfile.write(data.encode())
            else:
                self.wfile.write(b"{}")
            return

        # Serve static files from public_dir
        file_path = self.path.lstrip("/") or "index.html"
        full_path = os.path.join(self.server.public_dir, file_path)

        if os.path.exists(full_path) and os.path.isfile(full_path):
            self.send_response(200)
            if full_path.endswith(".html"):
                self.send_header("Content-Type", "text/html")
            elif full_path.endswith(".js"):
                self.send_header("Content-Type", "application/javascript")
            elif full_path.endswith(".css"):
                self.send_header("Content-Type", "text/css")
            else:
                self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            with open(full_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)


class MaintenanceServer:
    """Manages a temporary maintenance web server with polling support."""

    def __init__(self, port: int = 8080, public_dir: str = "dist") -> None:
        self.port: int = port
        self.public_dir: str = public_dir
        self.server: Optional[CustomHTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.logs: List[str] = []

    def start(self) -> None:
        """Starts the maintenance server in a separate thread."""
        bind_address = (
            "::" if CustomHTTPServer.address_family == socket.AF_INET6 else "0.0.0.0"
        )
        self.server = CustomHTTPServer((bind_address, self.port), StatusHandler)
        self.server.public_dir = self.public_dir
        self.server.current_status = {
            "status": "Starting...",
            "progress": 0,
            "logs": [],
        }

        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        self.update_status("Maintenance server started", 0)

    def stop(self) -> None:
        """Stops the maintenance server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.thread:
            self.thread.join()
            self.thread = None

    def update_status(self, status: str, progress: int) -> None:
        """Updates the status for polling clients."""
        self.logs.append(status)
        if len(self.logs) > 10:
            self.logs.pop(0)

        status_data = {
            "status": status,
            "progress": progress,
            "logs": self.logs,
            "timestamp": time.time(),
        }

        if self.server:
            self.server.current_status = status_data


def load_config(config_path: str = "config.json") -> Dict[str, str]:
    """Loads configuration from a JSON file.

    Args:
        config_path: The path to the configuration file.

    Returns:
        A dictionary containing the configuration settings.
    """
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r") as config_file:
        return json.load(config_file)


def run_shell_command(command: str, working_directory: Optional[str] = None) -> bool:
    """Executes a shell command and handles potential errors.

    Args:
        command: The shell command to execute.
        working_directory: The directory in which to execute the command.

    Returns:
        True if the command executed successfully, False otherwise.
    """
    try:
        subprocess.run(
            command,
            shell=True,
            check=True,
            cwd=working_directory,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as error:
        print(f"Error executing command: {command}\n{error.stderr}")
        return False


def get_latest_github_release(repository: str) -> Optional[str]:
    """Fetches the latest release tag from the GitHub API.

    Args:
        repository: The GitHub repository in 'owner/repo' format.

    Returns:
        The latest release tag name, or None if the request fails.
    """
    api_url: str = f"https://api.github.com/repos/{repository}/releases/latest"
    request: urllib.request.Request = urllib.request.Request(api_url)
    request.add_header("User-Agent", "Python-Urllib-Updater")

    try:
        with urllib.request.urlopen(request) as response:
            release_data: Dict = json.loads(response.read().decode())
            return release_data.get("tag_name")
    except Exception as error:
        print(f"Failed to fetch release: {error}")
        return None


def execute_deployment() -> None:
    """Main execution flow for checking updates and deploying new releases."""
    config: Dict[str, str] = load_config()

    repository: str = config["REPO"]
    service_name: str = config["SERVICE_NAME"]
    target_directory: str = config["TARGET_DIR"]
    state_file_path: str = config["STATE_FILE"]
    maintenance_port: int = int(config.get("MAINTENANCE_PORT", 8080))

    latest_release_tag: Optional[str] = get_latest_github_release(repository)
    if not latest_release_tag:
        sys.exit(1)

    current_installed_tag: str = ""
    if os.path.exists(state_file_path):
        with open(state_file_path, "r") as state_file:
            current_installed_tag = state_file.read().strip()

    if latest_release_tag == current_installed_tag:
        print(f"No update needed. Current: {current_installed_tag}")
        return

    print(f"New release found: {latest_release_tag}. Updating...")

    maintenance = MaintenanceServer(port=maintenance_port, public_dir="dist")

    # Ensure web assets are built
    if not os.path.exists("dist"):
        print("Building web assets...")
        run_shell_command("npm run build")

    maintenance.start()
    maintenance.update_status(f"Stopping {service_name}...", 10)

    if not run_shell_command(f"sudo systemctl stop {service_name}"):
        maintenance.update_status("Failed to stop service.", 10)
        maintenance.stop()
        sys.exit(1)

    git_update_commands: List[Dict] = [
        {
            "cmd": "git fetch --tags --all",
            "msg": "Fetching latest updates...",
            "prog": 30,
        },
        {
            "cmd": f"git checkout tags/{latest_release_tag}",
            "msg": f"Switching to {latest_release_tag}...",
            "prog": 60,
        },
    ]

    deployment_successful: bool = True
    for step in git_update_commands:
        maintenance.update_status(step["msg"], step["prog"])
        if not run_shell_command(step["cmd"], working_directory=target_directory):
            deployment_successful = False
            maintenance.update_status(f"Error during: {step['msg']}", step["prog"])
            break

    if deployment_successful:
        maintenance.update_status("Finalizing update...", 80)
        # Here you could add more steps like npm install or migrations

    maintenance.update_status(f"Restarting {service_name}...", 90)
    run_shell_command(f"sudo systemctl start {service_name}")

    if deployment_successful and latest_release_tag:
        with open(state_file_path, "w") as state_file:
            state_file.write(latest_release_tag)
        maintenance.update_status("Update complete!", 100)
        print(f"Successfully updated to {latest_release_tag}")
    else:
        print("Update failed during git operations.")
        maintenance.stop()
        sys.exit(1)

    time.sleep(2)  # Give user a moment to see 100%
    maintenance.stop()


def run_deployment_loop() -> None:
    """Continuously checks for updates and deploys new releases every 2 minutes."""
    print("Starting Git Auto Deployer loop (checking every 2 minutes)...")
    while True:
        try:
            execute_deployment()
        except Exception as error:
            print(f"Error during deployment check: {error}")

        time.sleep(120)


if __name__ == "__main__":
    run_deployment_loop()
