#!/bin/bash

# Get the directory of the script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
log_file="$script_dir/command_output.log"

# Run the Django management commands in the specified order,
# capturing the output and appending it to the log file
{
    echo "Current working directory: $(pwd)"
    echo "-------------------"

    echo "Running 'makemigrations'..."
    python manage.py makemigrations

    echo "Running 'migrate'..."
    python manage.py migrate

    echo "Running 'loaddata users_permission'..."
    python manage.py loaddata "$script_dir/users_permission.json"

    echo "Running 'loaddata users_role'..."
    python manage.py loaddata "$script_dir/users_role.json"

    echo "Running 'loaddata users'..."
    python manage.py loaddata "$script_dir/users.json"

    echo "Running 'loaddata users_userprofile'..."
    python manage.py loaddata "$script_dir/users_userprofile.json"

    echo "Running 'loaddata components_vulnerability'..."
    python manage.py loaddata "$script_dir/components_vulnerability.json"

    echo "Running 'loaddata components_client'..."
    python manage.py loaddata "$script_dir/components_client.json"

    echo "Running 'loaddata components_template'..."
    python manage.py loaddata "$script_dir/components_template.json"

    echo "Running 'loaddata assessment_structure'..."
    python manage.py loaddata "$script_dir/assessment_structure.json"
    
    echo "Running 'loaddata assessment_statuses'..."
    python manage.py loaddata "$script_dir/assessment_statuses.json"

    echo "Running 'loaddata taskstatus'..."
    python manage.py loaddata "$script_dir/taskstatus.json"

} 2>&1 | tee "$log_file"

echo "Command output has been saved to: $log_file"