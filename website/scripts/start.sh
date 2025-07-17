#!/bin/bash

cd "$(dirname "$0")/../.."

check_docker_with_retry() {
    while true; do
        echo "Checking Docker availability..."
        if docker version >/dev/null 2>&1; then
            echo "Docker is available."
            return 0
        else
            echo ""
            echo "Docker is not running or not installed."
            echo "Please start Docker Desktop and wait for it to fully load."
            echo ""
            read -p "Press Enter to check again, or Ctrl+C to exit..."
            echo ""
        fi
    done
}

check_docker_for_db_with_retry() {
    while true; do
        echo "Checking Docker availability for database..."
        if docker version >/dev/null 2>&1; then
            echo "Docker is available for database container."
            return 0
        else
            echo ""
            echo "Docker is not running - needed for database container."
            echo "Please start Docker Desktop and wait for it to fully load."
            echo ""
            read -p "Press Enter to check again, or Ctrl+C to exit..."
            echo ""
        fi
    done
}

while true; do
    read -p "Enter environment (dev/prod/server): " ENV
    ENV=$(echo "$ENV" | xargs)
    if [[ "$ENV" == "dev" ]]; then
        while true; do
            read -p "Do you want to use only Docker for development (yes/no/back)?: " USE_DOCKER
            USE_DOCKER=$(echo "$USE_DOCKER" | xargs)
            if [[ "$USE_DOCKER" == "yes" ]]; then
                check_docker_with_retry
                cd website/docker/website-dev
                export ENVIRONMENT=dev
                echo "Running: docker-compose up"
                docker-compose up
                if [ $? -ne 0 ]; then
                    echo ""
                    echo "ERROR: Docker compose failed!"
                    read -p "Press Enter to exit..."
                fi
                exit 0
            elif [[ "$USE_DOCKER" == "no" ]]; then
                check_docker_for_db_with_retry
                SCRIPTS_ROOT="$(pwd)/website"
                if command -v gnome-terminal &> /dev/null; then
                    gnome-terminal \
                        --tab --title="Database" -- bash -c "cd \"$SCRIPTS_ROOT/docker/website-dev\" && export ENVIRONMENT=dev && docker-compose up db; exec bash" \
                        --tab --title="Frontend" -- bash -c "cd \"$SCRIPTS_ROOT/frontend\" && export ENVIRONMENT=dev && npm install && npm audit fix && npm run dev; exec bash" \
                        --tab --title="Backend" -- bash -c "cd \"$SCRIPTS_ROOT/backend\" && export ENVIRONMENT=dev && poetry install && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8018; exec bash"
                elif command -v konsole &> /dev/null; then
                    konsole \
                        --new-tab -p tabtitle="Database" -e bash -c "cd \"$SCRIPTS_ROOT/docker/website-dev\" && export ENVIRONMENT=dev && docker-compose up db" \
                        --new-tab -p tabtitle="Frontend" -e bash -c "cd \"$SCRIPTS_ROOT/frontend\" && export ENVIRONMENT=dev && npm install && npm audit fix && npm run dev" \
                        --new-tab -p tabtitle="Backend" -e bash -c "cd \"$SCRIPTS_ROOT/backend\" && export ENVIRONMENT=dev && poetry install && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8018"
                elif command -v x-terminal-emulator &> /dev/null; then
                    x-terminal-emulator -T "Database" -e bash -c "cd \"$SCRIPTS_ROOT/docker/website-dev\" && export ENVIRONMENT=dev && docker-compose up db" &
                    x-terminal-emulator -T "Frontend" -e bash -c "cd \"$SCRIPTS_ROOT/frontend\" && export ENVIRONMENT=dev && npm install && npm audit fix && npm run dev" &
                    x-terminal-emulator -T "Backend" -e bash -c "cd \"$SCRIPTS_ROOT/backend\" && export ENVIRONMENT=dev && poetry install && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8018" &
                else
                    echo "No multi-tab terminal found. Running all services in the current terminal."
                    (cd website/docker/website-dev && export ENVIRONMENT=dev && docker-compose up db &) 
                    (cd website/frontend && export ENVIRONMENT=dev && npm install && npm audit fix && npm run dev &)
                    (cd website/backend && export ENVIRONMENT=dev && poetry install && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8018)
                fi
                exit 0
            elif [[ "$USE_DOCKER" == "back" ]]; then
                break
            else
                echo "Invalid choice. Please enter 'yes', 'no', or 'back'."
            fi
        done
    elif [[ "$ENV" == "prod" ]]; then
        check_docker_with_retry
        cd website/docker/website-prod
        export ENVIRONMENT=prod
        echo "Running: docker-compose up"
        docker-compose up
        if [ $? -ne 0 ]; then
            echo ""
            echo "ERROR: Docker compose failed!"
            read -p "Press Enter to exit..."
        fi
        exit 0
    elif [[ "$ENV" == "server" ]]; then
        check_docker_with_retry
        cd website/docker/website-server
        export ENVIRONMENT=server
        echo "Running: docker-compose up"
        docker-compose up
        if [ $? -ne 0 ]; then
            echo ""
            echo "ERROR: Docker compose failed!"
            read -p "Press Enter to exit..."
        fi
        exit 0
    else
        echo "Invalid environment. Please enter 'dev', 'prod', or 'server'."
    fi
done