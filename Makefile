# Chat System Makefile
# -----------------------------

VENV := .venv/bin
export PATH := $(VENV):$(PATH)

default: help

# Core Commands
# -----------------------------

install: venv # Install all project dependencies
	@$(VENV)/pip3 install -U -r requirements.txt;

run-server: # Run the chat server
	@echo "Checking for existing server instances..."
	@lsof -i :5555 -t | xargs kill 2>/dev/null || true
	@echo "Starting server..."
	@source .venv/bin/activate && PYTHONPATH=src python src/server/server.py

run-client: # Run the chat client (usage: make run-client CLIENT_ID=your_id SERVER_IP=x.x.x.x)
	@source .venv/bin/activate && PYTHONPATH=src python src/client/main.py $(CLIENT_ID) $(SERVER_IP)

test: # Run all tests
	@echo "Running all tests..."
	@$(VENV)/pytest tests/ --cov=src --cov-report term-missing --cov-fail-under=80 --cov-config=.coveragerc

# Development Tools
# -----------------------------

install-dev: install # Install development tools
	@$(VENV)/pip3 install -U -r devtools_requirements.txt;

fix-style: # Fix style issues
	@$(VENV)/isort src;
	@$(VENV)/black src;

report-issues: # Report code health issues
	-@$(VENV)/mypy src;
	-@$(VENV)/pylint src;


# Utility
# -----------------------------

show-ip: # Show the server's IP address
	@echo "Server IP Addresses:"
	@echo "----------------"
	@ifconfig | grep "inet " | grep -v 127.0.0.1

venv: # Create virtual environment if it doesn't exist
	@test -d .venv || python3 -m venv .venv;

clean: # Clean up cache files and directories
	@find . -name "*.pyc" -exec rm -f {} \;
	@find . -name "__pycache__" -type d -exec rm -rf {} +;
	@find . -name ".pytest_cache" -type d -exec rm -rf {} +;
	@find . -name ".mypy_cache" -type d -exec rm -rf {} +;
	@find . -name ".venv" -type d -exec rm -rf {} +;

help: # Show available make targets
	@echo "Chat System Make Targets\n"
	@echo "Core Commands:\n--------------"
	@echo "\033[1;32minstall\033[00m: Install all project dependencies"
	@echo "\033[1;32mrun-server\033[00m: Run the chat server"
	@echo "\033[1;32mrun-client\033[00m: Run the chat client"
	@echo "\033[1;32mrun-client-gui\033[00m: Run the GUI chat client"
	@echo "\033[1;32mtest\033[00m: Run all tests"
	@echo "\n"
	@echo "Development Tools:\n------------------"
	@echo "\033[1;32minstall-dev\033[00m: Install development tools"
	@echo "\033[1;32mfix-style\033[00m: Fix code style issues"
	@echo "\033[1;32mreport-issues\033[00m: Report code health issues"
	@echo "\n"
	@echo "\n"
	@echo "Utility:\n--------"
	@echo "\033[1;32mvenv\033[00m: Create virtual environment if it doesn't exist"
	@echo "\033[1;32mclean\033[00m: Clean up cache files and directories"
	@echo "\033[1;32mhelp\033[00m: Show this help message"


# PHONY Targets
# -----------------------------

.PHONY: help install test style run-server run-client run-client-gui clean venv show-ip
