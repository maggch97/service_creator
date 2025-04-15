#!/usr/bin/env python3
"""
Service Creator Script

This script creates a systemd service that runs at startup.
Usage: python service_creator.py command_file service_name [working_directory]

Parameters:
    command_file: Path to a file containing the command to run
    service_name: Name for the systemd service
    working_directory: (Optional) Directory where the command should run
"""

import sys
import os
import subprocess
from pathlib import Path

def create_service(command_file, service_name, working_directory=None):
    """
    Creates a systemd service using the command from command_file 
    with the given service_name and optional working_directory.
    """
    # Validate inputs
    if not os.path.exists(command_file):
        print(f"Error: Command file '{command_file}' not found.")
        return False
    
    # Read command from file
    with open(command_file, 'r') as f:
        command = f.read().strip()
    
    if not command:
        print("Error: Command file is empty.")
        return False
    
    # Make service name safe - remove any special characters and spaces
    service_name = ''.join(c for c in service_name if c.isalnum() or c in '-_')
    if not service_name:
        print("Error: Service name contains no valid characters.")
        return False
    
    service_filename = f"{service_name}.service"
    service_path = f"/etc/systemd/system/{service_filename}"
    
    # Get absolute path for command if it's a script file
    if ' ' not in command and os.path.exists(command):
        command = os.path.abspath(command)
    
    # Prepare service file content
    service_content = f"""[Unit]
Description={service_name} service
After=network.target

[Service]
Type=simple
ExecStart={command}
"""
    
    # Add working directory if specified
    if working_directory:
        if os.path.isdir(working_directory):
            working_directory = os.path.abspath(working_directory)
            service_content += f"WorkingDirectory={working_directory}\n"
        else:
            print(f"Warning: Working directory '{working_directory}' does not exist.")
    
    service_content += """Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

    # Write temporary service file
    temp_service_path = f"/tmp/{service_filename}"
    with open(temp_service_path, 'w') as f:
        f.write(service_content)
    
    # Check if we have root privileges
    if os.geteuid() != 0:
        print("This script needs root privileges to create a system service.")
        print(f"Service file created at: {temp_service_path}")
        print(f"Run the following commands to install the service:")
        print(f"sudo mv {temp_service_path} {service_path}")
        print(f"sudo systemctl daemon-reload")
        print(f"sudo systemctl enable {service_filename}")
        print(f"sudo systemctl start {service_filename}")
        return True
    
    # If we have root privileges, install the service
    try:
        # Move service file to system directory
        subprocess.run(['mv', temp_service_path, service_path], check=True)
        
        # Reload systemd, enable and start the service
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'enable', service_filename], check=True)
        subprocess.run(['systemctl', 'start', service_filename], check=True)
        
        print(f"Service '{service_name}' has been created and enabled.")
        print(f"You can check its status with: sudo systemctl status {service_filename}")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to install service. {e}")
        return False

def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python service_creator.py command_file service_name [working_directory]")
        sys.exit(1)
    
    command_file = sys.argv[1]
    service_name = sys.argv[2]
    working_directory = sys.argv[3] if len(sys.argv) == 4 else None
    
    success = create_service(command_file, service_name, working_directory)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
