#!/bin/bash

# Get the directory of the script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
log_file="$script_dir/setup.log"

# Exit on any error
set -e

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print info message
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Print success message
print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Print warning message
print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Print error message
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Start of script execution
print_status "Starting Threat Track database setup..."
print_status "Current working directory: $(pwd)"
print_status "Script directory: $script_dir"

# Create a fresh log file with timestamp
echo "=== Threat Track Database Setup - $(date) ===" > "$log_file"

# Run a command with logging and exit on failure
run_command() {
    local description="$1"
    local command="$2"

    print_status "$description"
    echo "-------------------" >> "$log_file"
    echo "Running: $description" >> "$log_file"
    echo "Command: $command" >> "$log_file"

    if eval "$command" >> "$log_file" 2>&1; then
        print_success "$description completed"
    else
        print_error "$description failed"
        echo "Check $log_file for details"
        exit 1
    fi
}

# Run Django management commands in order
{
    run_command "Making migrations" "python manage.py makemigrations"
    run_command "Running migrations" "python manage.py migrate"

    run_command "Loading user permissions" "python manage.py loaddata '$script_dir/users_permission.json'"
    run_command "Loading user roles" "python manage.py loaddata '$script_dir/users_role.json'"
    run_command "Loading default users" "python manage.py loaddata '$script_dir/users.json'"
    run_command "Loading user profiles" "python manage.py loaddata '$script_dir/users_userprofile.json'"
    run_command "Loading vulnerability components" "python manage.py loaddata '$script_dir/components_vulnerability.json'"
    run_command "Loading client components" "python manage.py loaddata '$script_dir/components_client.json'"
    run_command "Loading template components" "python manage.py loaddata '$script_dir/components_template.json'"
    run_command "Loading assessment structures" "python manage.py loaddata '$script_dir/assessment_structure.json'"
    run_command "Loading assessment statuses" "python manage.py loaddata '$script_dir/assessment_statuses.json'"
    run_command "Loading task statuses" "python manage.py loaddata '$script_dir/taskstatus.json'"

    run_command "Collecting static files" "python manage.py collectstatic --noinput"

    echo ""
    print_success "Database setup completed successfully"
    echo ""
    print_status "Setup Summary:"
    print_status "Database migrated"
    print_status "Default admin user created"
    print_status "All permissions and roles loaded"
    print_status "Components and templates loaded"
    print_status "Static files collected"
    echo ""
    print_status "Default Login Credentials:"
    print_status "Username: admin"
    print_status "Password: admin"
    echo ""
    print_warning "Remember to change the admin password in production"
    print_status "Setup log saved to: $log_file"
} 2>&1

# Final log message
echo "Command output has been saved to: $log_file"
