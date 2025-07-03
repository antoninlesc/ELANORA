#!/bin/bash

cd "$(dirname "$0")/../.."

check_docker() {
    echo "Checking Docker availability..."
    if docker version >/dev/null 2>&1; then
        echo "Docker is available."
        return 0
    else
        echo ""
        echo "ERROR: Docker is not running or not installed."
        echo "Please start Docker and try again."
        echo ""
        read -p "Press Enter to continue..."
        return 1
    fi
}

check_docker_for_db() {
    echo "Checking Docker availability for database..."
    if docker version >/dev/null 2>&1; then
        echo "Docker is available for database container."
        return 0
    else
        echo "Docker is not available - will need local MySQL server."
        return 1
    fi
}

while true; do
    read -p "Enter environment (dev/prod/server): " ENV
    ENV=$(echo "$ENV" | xargs)
    if [[ "$ENV" == "dev" ]]; then
        while true; do
            read -p "Do you want to use only Docker for development (yes/no/back)?: " USE_DOCKER
            USE_DOCKER=$(echo "$USE_DOCKER" | xargs)
            if [[ "$USE_DOCKER" == "yes" ]]; then
                if ! check_docker; then
                    exit 1
                fi
                cd website/docker/website-dev
                ENV=dev.docker docker-compose up
                exit 0
            elif [[ "$USE_DOCKER" == "no" ]]; then
                if ! check_docker_for_db; then
                    echo ""
                    echo "WARNING: Docker is not available for database container."
                    echo "Please ensure you have a local MySQL server running or start Docker."
                    echo ""
                    read -p "Continue anyway? (yes/no): " CONTINUE
                    if [[ "$CONTINUE" != "yes" ]]; then
                        exit 1
                    fi
                    DOCKER_AVAILABLE=false
                else
                    DOCKER_AVAILABLE=true
                fi
                
                SCRIPTS_ROOT="$(pwd)/website"
                
                if [[ "$DOCKER_AVAILABLE" == "true" ]]; then
                    # Use Docker for database
                    if command -v gnome-terminal &> /dev/null; then
                        gnome-terminal \
                            --tab --title="Database" -- bash -c "cd \"$SCRIPTS_ROOT/docker/website-dev\" && ENV=dev docker-compose up db; exec bash" \
                            --tab --title="Frontend" -- bash -c "cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev; exec bash" \
                            --tab --title="Backend" -- bash -c "cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash"
                    elif command -v konsole &> /dev/null; then
                        konsole \
                            --new-tab -p tabtitle="Database" -e bash -c "cd \"$SCRIPTS_ROOT/docker/website-dev\" && ENV=dev docker-compose up db" \
                            --new-tab -p tabtitle="Frontend" -e bash -c "cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev" \
                            --new-tab -p tabtitle="Backend" -e bash -c "cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018"
                    elif command -v x-terminal-emulator &> /dev/null; then
                        x-terminal-emulator -T "Database" -e bash -c "cd \"$SCRIPTS_ROOT/docker/website-dev\" && ENV=dev docker-compose up db" &
                        x-terminal-emulator -T "Frontend" -e bash -c "cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev" &
                        x-terminal-emulator -T "Backend" -e bash -c "cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018" &
                    else
                        echo "No multi-tab terminal found. Running all services in the current terminal."
                        (cd website/docker/website-dev && ENV=dev docker-compose up db &) 
                        (cd website/frontend && ENV=dev npm install && npm run dev &)
                        (cd website/backend && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018)
                    fi
                else
                    # No Docker - use local setup
                    if command -v gnome-terminal &> /dev/null; then
                        gnome-terminal \
                            --tab --title="Local Setup" -- bash -c "echo 'Please start your local MySQL server manually, then press any key' && read -n 1 && echo 'Ready for development!'; exec bash" \
                            --tab --title="Frontend" -- bash -c "cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev; exec bash" \
                            --tab --title="Backend" -- bash -c "cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash"
                    elif command -v konsole &> /dev/null; then
                        konsole \
                            --new-tab -p tabtitle="Local Setup" -e bash -c "echo 'Please start your local MySQL server manually, then press any key' && read -n 1 && echo 'Ready for development!'" \
                            --new-tab -p tabtitle="Frontend" -e bash -c "cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev" \
                            --new-tab -p tabtitle="Backend" -e bash -c "cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018"
                    elif command -v x-terminal-emulator &> /dev/null; then
                        x-terminal-emulator -T "Local Setup" -e bash -c "echo 'Please start your local MySQL server manually, then press any key' && read -n 1 && echo 'Ready for development!'" &
                        x-terminal-emulator -T "Frontend" -e bash -c "cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev" &
                        x-terminal-emulator -T "Backend" -e bash -c "cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018" &
                    else
                        echo "No multi-tab terminal found. Please start your local MySQL server manually."
                        echo "Press any key when ready..."
                        read -n 1
                        (cd website/frontend && ENV=dev npm install && npm run dev &)
                        (cd website/backend && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018)
                    fi
                fi
                exit 0
            elif [[ "$USE_DOCKER" == "back" ]]; then
                break
            else
                echo "Invalid choice. Please enter 'yes', 'no', or 'back'."
            fi
        done
    elif [[ "$ENV" == "prod" ]]; then
        if ! check_docker; then
            exit 1
        fi
        cd website/docker/website-prod
        ENV=prod docker-compose up
        exit 0
    elif [[ "$ENV" == "server" ]]; then
        if ! check_docker; then
            exit 1
        fi
        cd website/docker/website-server
        ENV=server docker-compose up
        exit 0
    else
        echo "Invalid environment. Please enter 'dev', 'prod', or 'server'."
    fi
done