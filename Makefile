# Chat System Makefile
# -----------------------------

VENV := .venv/bin
export PATH := $(VENV):$(PATH)

default: help

# Core Commands
# -----------------------------

install: venv # Install all project dependencies
	@$(VENV)/pip3 install -U -r requirements.txt;

run-server: # Run the main chat server
	@cd src/server && source ../../.venv/bin/activate && python main.py

run-client: # Run the main chat client
	@cd src/client && source ../../.venv/bin/activate && python main.py

test: # Run all tests
	@echo "Running protocol tests..."
	@cd src/protocol && $(VENV)/pytest --cov=. --cov-report term-missing --cov-fail-under=80
	@echo "Running client tests..."
	@cd src/client && $(VENV)/pytest


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


# Protocol Testing
# -----------------------------

run-protocol-server: # Run the protocol test server
	@cd src/protocol && source ../../.venv/bin/activate && python server.py

run-protocol-client: # Run the protocol test client (optional: specify CLIENT_ID=your_id)
	@cd src/protocol && source ../../.venv/bin/activate && python client.py $(CLIENT_ID)


# Utility
# -----------------------------

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
	@echo "\033[1;32mrun-server\033[00m: Run the main chat server"
	@echo "\033[1;32mrun-client\033[00m: Run the main chat client"
	@echo "\033[1;32mtest\033[00m: Run all tests"
	@echo "\n"
	@echo "Development Tools:\n------------------"
	@echo "\033[1;32minstall-dev\033[00m: Install development tools"
	@echo "\033[1;32mfix-style\033[00m: Fix code style issues"
	@echo "\033[1;32mreport-issues\033[00m: Report code health issues"
	@echo "\n"
	@echo "Protocol Testing:\n-----------------"
	@echo "\033[1;32mrun-protocol-server\033[00m: Run the protocol test server"
	@echo "\033[1;32mrun-protocol-client\033[00m: Run the protocol test client (optional: specify CLIENT_ID=your_id)"
	@echo "\n"
	@echo "Utility:\n--------"
	@echo "\033[1;32mvenv\033[00m: Create virtual environment if it doesn't exist"
	@echo "\033[1;32mclean\033[00m: Clean up cache files and directories"
	@echo "\033[1;32mhelp\033[00m: Show this help message"


# PHONY Targets
# -----------------------------

.PHONY: help install test style run-server run-client run-protocol-server run-protocol-client clean venv
