install:
	@echo "Preparing virtual environment..."
	@./venv_install.sh
	@echo "Created app directory '/opt/romopad/'"
	@mkdir /opt/romopad/
	@echo "Copying files..."
	@cp -R * /opt/romopad/
	@cp -R .venv /opt/romopad/
	@rm /opt/romopad/Makefile
	@rm -rf /opt/romopad/__pycache__
	@echo "File copying completed"
	@echo "Loading uinput moudule"
	@modprobe uinput
	@echo "Adding persistence for uinput module"
	@echo "uinput">/etc/modules-load.d/romopad.conf
	@echo "Adding input rules"
	@echo 'KERNEL=="uinput", GROUP="input", MODE:="0660"'>/etc/udev/rules.d/romopad.rules
	@udevadm control --reload-rules
	@udevadm trigger
	@echo "Installing systemd service romopad.service..."
	@cp romopad.service /etc/systemd/user/romopad.service
	@echo "Installation completed"

uninstall:
	@echo "Checking for files..."
	@if [ -d /opt/romopad ]; then rm -rf /opt/romopad && echo "Files removed"; else echo "No files found";fi
	@echo "Checking for service..."
	@if [ -f /etc/systemd/user/romopad.service ]; then rm /etc/systemd/user/romopad.service && echo "Removed systemd service."; else echo "No service found";fi
	@echo "Checking for romopad's uinput persistence exists..."
	@if [ -f /etc/modules-load.d/romopad.conf ]; then rm /etc/modules-load.d/romopad.conf && echo "Romopad's uinput persistence removed."; else echo "Persistence not found.";fi
	@echo "Checking for input rules.."
	@if [ -f /etc/udev/rules.d/romopad.rules ]; then rm /etc/udev/rules.d/romopad.rules && echo "Romopad's input rules removed."; else echo "Romopad's input rules not found.";fi
	@echo "Reloading input rules..."
	@udevadm control --reload-rules
	@udevadm trigger
	@echo "Removal complete."

