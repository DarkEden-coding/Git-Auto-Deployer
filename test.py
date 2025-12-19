import time
from auto_deploy import MaintenanceServer


def test_maintenance_server() -> None:
    """Cycles through statuses to test the maintenance server with polling."""
    import os

    if not os.path.exists("dist"):
        print("Warning: 'dist' directory not found. Please run 'npm run build' first.")
        # Fallback to web source for testing if dist is missing
        # Note: Tailwind styles won't work in raw source mode without Vite
        public_dir = "web"
    else:
        public_dir = "dist"

    server = MaintenanceServer(port=8080, public_dir=public_dir)

    print("Starting test server on http://localhost:8080")
    print("If localhost is not accessible, try http://127.0.0.1:8080")
    server.start()

    steps = [
        ("Checking for updates...", 10),
        ("Downloading latest release...", 30),
        ("Extracting files...", 50),
        ("Running migrations...", 70),
        ("Restarting services...", 90),
        ("Update complete!", 100),
    ]

    try:
        while True:
            for message, progress in steps:
                print(f"Update: {message} ({progress}%)")
                server.update_status(message, progress)
                time.sleep(2)
            print("Restarting status cycle...")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest interrupted.")
    finally:
        print("Stopping server.")
        server.stop()


if __name__ == "__main__":
    test_maintenance_server()
