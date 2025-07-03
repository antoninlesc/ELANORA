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
                ENV=dev.docker docker-compose up
                exit 0
            elif [[ "$USE_DOCKER" == "no" ]]; then
                check_docker_for_db_with_retry
                
                SCRIPTS_ROOT="$(pwd)/website"
                
                # Debug: Show which terminals are available
                echo "Detecting available terminal emulators..."
                
                # Use Docker for database, local for frontend/backend
                if command -v gnome-terminal &> /dev/null; then
                    echo "Using gnome-terminal"
                    # Use separate gnome-terminal commands for better compatibility
                    gnome-terminal --title="Database" -- bash -c "cd '$SCRIPTS_ROOT/docker/website-dev' && ENV=dev docker-compose up db; exec bash" 2>/dev/null &
                    sleep 0.5
                    gnome-terminal --title="Frontend" -- bash -c "cd '$SCRIPTS_ROOT/frontend' && ENV=dev npm install && npm run dev; exec bash" 2>/dev/null &
                    sleep 0.5
                    gnome-terminal --title="Backend" -- bash -c "cd '$SCRIPTS_ROOT/backend' && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash" 2>/dev/null &
                elif command -v konsole &> /dev/null; then
                    echo "Using konsole"
                    konsole \
                        --new-tab -p tabtitle="Database" -e bash -c "cd '$SCRIPTS_ROOT/docker/website-dev' && ENV=dev docker-compose up db; exec bash" \
                        --new-tab -p tabtitle="Frontend" -e bash -c "cd '$SCRIPTS_ROOT/frontend' && ENV=dev npm install && npm run dev; exec bash" \
                        --new-tab -p tabtitle="Backend" -e bash -c "cd '$SCRIPTS_ROOT/backend' && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash"
                elif command -v mate-terminal &> /dev/null; then
                    echo "Using mate-terminal"
                    mate-terminal \
                        --tab --title="Database" -e "bash -c 'cd \"$SCRIPTS_ROOT/docker/website-dev\" && ENV=dev docker-compose up db; exec bash'" \
                        --tab --title="Frontend" -e "bash -c 'cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev; exec bash'" \
                        --tab --title="Backend" -e "bash -c 'cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash'"
                elif command -v xfce4-terminal &> /dev/null; then
                    echo "Using xfce4-terminal"
                    xfce4-terminal \
                        --tab --title="Database" --command="bash -c 'cd \"$SCRIPTS_ROOT/docker/website-dev\" && ENV=dev docker-compose up db; exec bash'" \
                        --tab --title="Frontend" --command="bash -c 'cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev; exec bash'" \
                        --tab --title="Backend" --command="bash -c 'cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash'"
                elif command -v tilix &> /dev/null; then
                    echo "Using tilix"
                    tilix -w ~ -a session-add-down -x bash -c "cd \"$SCRIPTS_ROOT/docker/website-dev\" && ENV=dev docker-compose up db; exec bash" \
                          -a session-add-right -x bash -c "cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev; exec bash" \
                          -a session-add-down -x bash -c "cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash"
                elif command -v terminator &> /dev/null; then
                    echo "Using terminator"
                    terminator -T "Database" -x bash -c "cd \"$SCRIPTS_ROOT/docker/website-dev\" && ENV=dev docker-compose up db; exec bash" &
                    sleep 1
                    terminator -T "Frontend" -x bash -c "cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev; exec bash" &
                    sleep 1
                    terminator -T "Backend" -x bash -c "cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash" &
                elif [[ "$OSTYPE" == "darwin"* ]]; then
                    echo "Using macOS Terminal"
                    osascript <<EOF
tell application "Terminal"
    activate
    do script "cd \"$SCRIPTS_ROOT/docker/website-dev\" && ENV=dev docker-compose up db"
    do script "cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev" in (make new tab)
    do script "cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018" in (make new tab)
end tell
EOF
                else
                    echo "No supported multi-tab terminal found."
                    echo "Trying to open separate terminal windows..."
                    
                    # Try separate windows instead
                    if command -v gnome-terminal &> /dev/null; then
                        echo "Opening separate gnome-terminal windows..."
                        gnome-terminal --title="Database" -- bash -c "cd '$SCRIPTS_ROOT/docker/website-dev' && ENV=dev docker-compose up db; exec bash" 2>/dev/null &
                        gnome-terminal --title="Frontend" -- bash -c "cd '$SCRIPTS_ROOT/frontend' && ENV=dev npm install && npm run dev; exec bash" 2>/dev/null &
                        gnome-terminal --title="Backend" -- bash -c "cd '$SCRIPTS_ROOT/backend' && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash" 2>/dev/null &
                    elif command -v x-terminal-emulator &> /dev/null; then
                        echo "Opening separate x-terminal-emulator windows..."
                        x-terminal-emulator -T "Database" -e bash -c "cd '$SCRIPTS_ROOT/docker/website-dev' && ENV=dev docker-compose up db; exec bash" &
                        x-terminal-emulator -T "Frontend" -e bash -c "cd '$SCRIPTS_ROOT/frontend' && ENV=dev npm install && npm run dev; exec bash" &
                        x-terminal-emulator -T "Backend" -e bash -c "cd '$SCRIPTS_ROOT/backend' && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash" &
                    else
                        echo "Running all services in current terminal with background processes..."
                        echo "Starting Database in background..."
                        (cd website/docker/website-dev && ENV=dev docker-compose up db) &
                        echo "Starting Frontend in background..."
                        (cd website/frontend && ENV=dev npm install && npm run dev) &
                        echo "Starting Backend in foreground..."
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
        check_docker_with_retry
        cd website/docker/website-prod
        ENV=prod docker-compose up
        exit 0
    elif [[ "$ENV" == "server" ]]; then
        check_docker_with_retry
        cd website/docker/website-server
        ENV=server docker-compose up
        exit 0
    else
        echo "Invalid environment. Please enter 'dev', 'prod', or 'server'."
    fi
done