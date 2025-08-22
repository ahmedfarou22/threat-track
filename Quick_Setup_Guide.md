# Threat Track Setup Guide

This guide will walk you through setting up Threat Track using Docker.

## Prerequisites

### Install Docker

Before you begin, you need to have Docker installed on your system.

#### For Linux (Tested on: Ubuntu 24.04, kernel 6.11.0-29-generic)

**Reference System (for installation):**

- OS: Ubuntu 24.04 (x86_64)
- Kernel: Linux 6.11.0-29-generic
- CPU: 1 vCPU (KVM/QEMU)
- RAM: 1GB
- Storage: 8GB (1GB free recommended)

```bash
# Update package index
sudo apt update

# Install Docker
sudo apt install docker.io docker-compose-v2 -y

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group (optional, to run without sudo)
sudo usermod -aG docker $USER
```

## Clone the Repository

Before you begin, clone the repository to your local machine:

```bash
git clone https://github.com/ahmedfarou22/threat-track.git
cd threat-track
```

## Setup Instructions

### Environment Configuration

First, you need to set up your environment variables:

```bash
# Copy the example environment file
cp .env.example .env
```

### Environment Variables

Edit the `.env` file to configure your deployment. Here are the key variables you can customize:

#### Media Storage Configuration

- **MEDIA_HOST**: Custom host for media files (optional)
- **MEDIA_PORT**: Custom port for media files (optional, default: 8080)

For a basic local setup, the default values in `.env.example` work fine. The application runs on port 8080 by default, but you can change this in the `.env` file if needed.

### Start the Application

Run the following commands in your terminal from the project root directory:

```bash
# Build and start all services in detached mode
docker compose up --build -d
```

This command will:

- Build the Docker images
- Start the database, web application, and media services
- Run everything in the background

### Initialize the Database

After the containers are running, initialize the database:

```bash
# Execute the database setup script
docker compose exec app ./transfer_db/transfer_db.sh
```

This script will set up the database schema and create initial data.

### Access the Application

Once the setup is complete, you can access Threat Track at:

- **URL**: http://localhost:8000
- **Default Admin Username**: `admin`
- **Default Admin Password**: `admin`

⚠️ **Important**: Change the default admin password after your first login!

## Managing the Application

### Stop the Application

```bash
# Stop all running containers
docker compose stop
```

### Start the Application (after initial setup)

```bash
# Start existing containers
docker compose up -d
```
