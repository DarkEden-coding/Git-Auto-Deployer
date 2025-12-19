# 🚀 Git Auto Deployer

A simple, friendly app updater that monitors GitHub releases and automatically deploys updates to your server with a nice status page.

## ✨ Features

- **GitHub Monitoring**: Automatically checks for new release tags on your GitHub repository.
- **Service Management**: Gracefully stops and restarts your systemd service during updates.
- **Live Status Page**: Shows a maintenance page with real-time progress while updating.
- **Easy Setup**: Includes scripts to configure and install as a systemd timer.

## 🛠️ Quick Start

1. **Clone & Install**:
   ```bash
   git clone https://github.com/your-repo/Git-Auto-Deployer.git
   cd Git-Auto-Deployer
   ```

2. **Configure**:
   Run the config script to set up your repository and service details:
   ```bash
   uv run python setup_config.py
   ```

3. **Install as Service**:
   Generate the systemd service file:
   ```bash
   uv run python setup_service.py
   ```
   Follow the printed instructions to enable the service.

## 📦 Requirements

- **Python**: 3.10+
- **uv**: Recommended for fast package management
- **Node.js**: For building the status page frontend

## 📝 How it works

The script runs continuously in the background, checking the GitHub API for a new tag every 2 minutes. If a new release is found, it:
1. Builds the latest status page.
2. Starts a temporary maintenance server on port `8080`.
3. Stops your application service.
4. Performs a `git checkout` to the new tag.
5. Restarts your service and shuts down the maintenance page.

Enjoy stress-free deployments! 🥂
