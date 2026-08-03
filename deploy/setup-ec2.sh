#!/bin/bash
set -euo pipefail

echo "=== YT-Chatter EC2 Setup ==="

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt-get install -y docker-compose-plugin

# Install Nginx
sudo apt-get install -y nginx

# Install Certbot for HTTPS
sudo apt-get install -y certbot python3-certbot-nginx

# Create project directory
sudo mkdir -p /opt/yt-chatter
sudo chown $USER:$USER /opt/yt-chatter

echo "=== Setup complete ==="
echo "Log out and back in for Docker group to take effect."
echo "Then: cd /opt/yt-chatter && git clone <repo> ."
