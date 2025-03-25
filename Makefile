# Chat System Makefile
# -----------------------------

VENV := .venv/bin
export PATH := $(VENV):$(PATH)

default: help

# Core Commands
# -----------------------------

install: venv # Install all project dependencies
	@$(VENV)/pip3 install -U -r requirements.txt;
# No default values

# Helper function to check required parameters
check_defined = \
    $(strip $(foreach 1,$1, \
        $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
    $(if $(value $1),, \
        $(error Parameter '$1' is undefined. $(if $2,$2,)))

.PHONY: run-server run-client

run-server: # Run the chat server (usage: make run-server MODE={grpc|socket} PORT=port SERVER_ID=id [PEERS=peer_list])
	$(call check_defined, MODE, Please specify MODE={grpc|socket})
	$(call check_defined, PORT, Please specify PORT=<port_number>)
	$(call check_defined, SERVER_ID, Please specify SERVER_ID=<server_id>)
	@echo "Checking for existing server instances..."
	@lsof -i :$(PORT) -t | xargs kill 2>/dev/null || true
	@echo "Starting server with MODE=$(MODE), PORT=$(PORT), SERVER_ID=$(SERVER_ID), PEERS=$(PEERS)"
	@source .venv/bin/activate && PYTHONPATH=src python src/server/main.py --mode $(MODE) --port $(PORT) --server_id $(SERVER_ID) $(if $(PEERS),--peers $(PEERS),)

run-client: # Run the chat client (usage: make run-client MODE={grpc|socket} PORT=port CLIENT_ID=client_id SERVER_IP=ip)
	$(call check_defined, MODE, Please specify MODE={grpc|socket})
	$(call check_defined, PORT, Please specify PORT=<port_number>)
	$(call check_defined, CLIENT_ID, Please specify CLIENT_ID=<client_id>)
	$(call check_defined, SERVER_IP, Please specify SERVER_IP=<server_ip>)
	@echo "Starting client with MODE=$(MODE), PORT=$(PORT), CLIENT_ID=$(CLIENT_ID), SERVER_IP=$(SERVER_IP)"
	@source .venv/bin/activate && PYTHONPATH=src python src/client/main.py --mode $(MODE) --port $(PORT) --client_id $(CLIENT_ID) --server_addr $(SERVER_IP)

test: # Run all tests
	@echo "Running all tests..."
	@PYTHONPATH=src pytest tests/ --cov=src --cov-report term-missing --cov-fail-under=80 --cov-config=.coveragerc
test-report: # Generate and open HTML coverage report
	@echo "Generating coverage report..."
	@PYTHONPATH=src && $(VENV)/pytest tests/ --cov=src --cov-report html --cov-config=.coveragerc

benchmark: # Run protocol performance benchmarks
	@echo "Running protocol size benchmarks (json, custom, and grpc)..."
	@PYTHONPATH=. python benchmarks/protocol/protocol_size_benchmark.py
	@echo "\n\nRunning protocol json and custom benchmarks..."
	@mkdir -p benchmarks/protocol/results
	@PYTHONPATH=. python benchmarks/protocol/test_protocol_performance.py
	@echo "Benchmark results saved in benchmarks/protocol/results/"

# Protocol Commands
# -----------------------------

proto: # Generate Python code from all .proto files
	@echo "Generating Python code from protocol buffers..."
	@$(VENV)/python -m grpc_tools.protoc \
		-I./src/protocol/grpc \
		--python_out=./src/protocol/grpc \
		--grpc_python_out=./src/protocol/grpc \
		./src/protocol/grpc/*.proto
	@echo "Protocol buffers compiled successfully"

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
	@find . -name "*_pb2*.py" -exec rm -f {} \;

help: # Show available make targets
	@echo "Chat System Make Targets\n"
	@echo "Core Commands:\n--------------"
	@echo "\033[1;32minstall\033[00m: Install all project dependencies"
	@echo "\033[1;32minstall-dev\033[00m: Install development tools, pytest, pylint, mypy"
	@echo "\033[1;32mrun-server\033[00m: Run the chat server (e.x usage: make run-server MODE=grpc SERVER_ID=server1 PORT=5555 PEERS=127.0.0.1:5556,127.0.0.1:5557)"
	@echo "\033[1;32mrun-client\033[00m: Run the chat client (usage: make run-client MODE={grpc|socket} PORT=5555 CLIENT_ID=your_id SERVER_IP=x.x.x.x)"
	@echo "\033[1;32mrun-client-gui\033[00m: Run the GUI chat client"
	@echo "\033[1;32mtest\033[00m: Run all tests"
	@echo "\033[1;32mbenchmark\033[00m: Run protocol performance benchmarks"
	@echo "\n"
	@echo "gRPC Commands:\n--------------"
	@echo "\033[1;32mgenerate-grpc\033[00m: Generate gRPC stubs from proto files"
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


# gRPC Commands
# -----------------------------

generate-grpc: # Generate gRPC stubs from proto files
	@echo "Generating gRPC stubs..."
	@source .venv/bin/activate && python -m grpc_tools.protoc -I src/protocol/grpc \
		--python_out=src/protocol/grpc \
		--grpc_python_out=src/protocol/grpc \
		src/protocol/grpc/chat.proto

# PHONY Targets
# -----------------------------

.PHONY: help install install-dev test test-report benchmark fix-style run-server run-client run-client-gui clean venv show-ip generate-grpc
