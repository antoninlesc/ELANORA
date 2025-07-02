#!/bin/bash

cd "$(dirname "$0")/../.."

while true; do
    read -p "Enter environment (dev/prod/server): " ENV
    ENV=$(echo "$ENV" | xargs)
    if [[ "$ENV" == "dev" ]]; then
        while true; do
            read -p "Do you want to use only Docker for development (yes/no/back)?: " USE_DOCKER
            USE_DOCKER=$(echo "$USE_DOCKER" | xargs)
            if [[ "$USE_DOCKER" == "yes" ]]; then
                cd lsfb-website/docker/MDL-Corpus-dev
                ENV=dev.docker docker-compose up
                exit 0
            elif [[ "$USE_DOCKER" == "no" ]]; then
                SCRIPTS_ROOT="$(pwd)/lsfb-website"
                if command -v gnome-terminal &> /dev/null; then
                    gnome-terminal \
                        --tab --title="Database" -- bash -c "cd \"$SCRIPTS_ROOT/docker/MDL-Corpus-dev\" && ENV=dev docker-compose up db; exec bash" \
                        --tab --title="Frontend" -- bash -c "cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev; exec bash" \
                        --tab --title="Backend" -- bash -c "cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8008; exec bash"
                elif command -v konsole &> /dev/null; then
                    konsole \
                        --new-tab -p tabtitle="Database" -e bash -c "cd \"$SCRIPTS_ROOT/docker/MDL-Corpus-dev\" && ENV=dev docker-compose up db" \
                        --new-tab -p tabtitle="Frontend" -e bash -c "cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev" \
                        --new-tab -p tabtitle="Backend" -e bash -c "cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8008"
                elif command -v x-terminal-emulator &> /dev/null; then
                    x-terminal-emulator -T "Database" -e bash -c "cd \"$SCRIPTS_ROOT/docker/MDL-Corpus-dev\" && ENV=dev docker-compose up db" &
                    x-terminal-emulator -T "Frontend" -e bash -c "cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev" &
                    x-terminal-emulator -T "Backend" -e bash -c "cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8008" &
                else
                    echo "No multi-tab terminal found. Running all services in the current terminal."
                    (cd lsfb-website/docker/MDL-Corpus-dev && ENV=dev docker-compose up db &) 
                    (cd lsfb-website/frontend && ENV=dev npm install && npm run dev &)
                    (cd lsfb-website/backend && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8008)
                fi
                exit 0
            elif [[ "$USE_DOCKER" == "back" ]]; then
                break
            else
                echo "Invalid choice. Please enter 'yes', 'no', or 'back'."
            fi
        done
    elif [[ "$ENV" == "prod" ]]; then
        cd lsfb-website/docker/MDL-Corpus-prod
        ENV=prod docker-compose up
        exit 0
    elif [[ "$ENV" == "server" ]]; then
        cd lsfb-website/docker/MDL-Corpus-server
        ENV=server docker-compose up
        exit 0
    else
        echo "Invalid environment. Please enter 'dev', 'prod', or 'server'."
    fi
done