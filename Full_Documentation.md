# Threat Track Setup Guide

This guide will walk you through setting up Threat Track using Docker.

## Prerequisites

### Install Docker

Before you begin, you need to have Docker installed on your system.

#### For Windows:

1. Download Docker Desktop from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Run the installer and follow the setup wizard
3. Restart your computer when prompted
4. Launch Docker Desktop and wait for it to start

#### For macOS:

1. Download Docker Desktop from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Open the downloaded `.dmg` file
3. Drag Docker to your Applications folder
4. Launch Docker from Applications and follow the setup instructions

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

#### Deployment Mode

- **COMPOSE_PROFILES**: Choose your deployment scenario:
  - `LOCAL,media` - Docker PostgreSQL + Local media container (recommended for development)
  - `LOCAL,S3` - Docker PostgreSQL + S3 storage
  - `AZURE,BLOB` - Azure PostgreSQL + Azure Blob storage
  - `AWS,S3` - AWS RDS + AWS S3 storage
  - `development` - Development mode with hot reloading

#### Application Settings

- **DEBUG**: Set to `True` for development, `False` for production
- **DJANGO_SECRET_KEY**: Your Django secret key (optional, will be auto-generated if not provided)
- **DJANGO_ALLOWED_HOSTS**: Comma-separated list of allowed hosts (e.g., `localhost,127.0.0.1,app,your-domain.com`)

  ⚠️ **Important**: You need to add your host to `DJANGO_ALLOWED_HOSTS` if it's not already listed. If you're accessing the application from a different domain or IP address, make sure to include it in this variable.

#### Database Configuration

- **DATABASE_TYPE**: Choose between `LOCAL`, `AZURE`, or `AWS`
- **DB_PASSWORD**: Password for local PostgreSQL database
- **DATABASE_CONFIGURATION**: Connection string for external databases

#### Media Storage Configuration

- **MEDIA_STORAGE_TYPE**: Choose between `LOCAL`, `BLOB`, or `S3`
- **MEDIA_HOST**: Custom host for media files (optional)
- **MEDIA_PORT**: Custom port for media files (optional, default: 8080)

For a basic local setup, the default values in `.env.example` work fine. The application runs on port 8080 by default, but you can change this in the `.env` file if needed. Just make sure to:

- Set `DEBUG=True` if you're developing
- Update `DJANGO_ALLOWED_HOSTS` if you're accessing from a different domain

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

### View Logs

```bash
# View logs for all services
docker compose logs

# View logs for a specific service
docker compose logs app
docker compose logs db
```

### Restart the Application

```bash
# Restart all services
docker compose restart

# Restart a specific service
docker compose restart app
```

## Troubleshooting

### Port Conflicts

If you encounter port conflicts, you can modify the ports in `docker-compose.yml` or stop services using those ports.

### Permission Issues

On Linux, if you encounter permission issues, make sure your user is in the docker group:

```bash
sudo usermod -aG docker $USER
```

Then log out and log back in.

### Database Issues

If you encounter database issues, you can reset the database:

```bash
docker compose down -v  # This removes volumes
docker compose up --build -d
docker compose exec app ./transfer_db/transfer_db.sh
```

## Next Steps

After successful setup:

1. Log in with the default admin credentials
2. Change the admin password
3. Create additional user accounts as needed
4. Start using Threat Track for your penetration testing assessments
