#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to check for Python installation
check_and_install_python() {
	echo "Checking for Python installation..."
	if ! command -v python &>/dev/null && ! command -v python3 &>/dev/null && ! command -v py &>/dev/null; then
		echo "Python is not installed. Attempting to install Python..."
		chmod +x install_python_linux_macos.sh
		./install_python_linux_macos.sh
	else
		echo "Python is already installed."
	fi
}

# Function to ensure pip is installed and up-to-date
install_or_update_pip() {
	echo "Ensuring pip is installed and up-to-date..."
	if command -v python &>/dev/null; then
		python -m ensurepip --upgrade || true
		python -m pip install --upgrade pip
	elif command -v python3 &>/dev/null; then
		python3 -m ensurepip --upgrade || true
		python3 -m pip install --upgrade pip
	elif command -v py &>/dev/null; then
		py -m ensurepip --upgrade || true
		py -m pip install --upgrade pip
	else
		echo "Error: Unable to locate Python or pip."
		exit 1
	fi
}

# Main function for execution
main() {
	check_and_install_python
	install_or_update_pip

	# Run the Python build script with `-w` argument
	if command -v python &>/dev/null; then
		python build.py -w
	elif command -v python3 &>/dev/null; then
		python3 build.py -w
	elif command -v py &>/dev/null; then
		py build.py -w
	else
		echo "Error: Unable to execute build.py."
		exit 1
	fi
}

# Execute the main function
main