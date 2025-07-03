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
                    echo "Using gnome-terminal with tabs"
                    # Method 1: Try the modern syntax first
                    gnome-terminal --tab --title="Database" --working-directory="$SCRIPTS_ROOT/docker/website-dev" -- bash -c "ENV=dev docker-compose up db; exec bash" \
                                   --tab --title="Frontend" --working-directory="$SCRIPTS_ROOT/frontend" -- bash -c "ENV=dev npm install && npm run dev; exec bash" \
                                   --tab --title="Backend" --working-directory="$SCRIPTS_ROOT/backend" -- bash -c "ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash" 2>/dev/null || \
                    # Method 2: Fallback to older syntax
                    gnome-terminal --tab -t "Database" -e "bash -c 'cd \"$SCRIPTS_ROOT/docker/website-dev\" && ENV=dev docker-compose up db; exec bash'" \
                                   --tab -t "Frontend" -e "bash -c 'cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev; exec bash'" \
                                   --tab -t "Backend" -e "bash -c 'cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash'" 2>/dev/null || \
                    # Method 3: Use separate windows as fallback
                    {
                        echo "Tab syntax not supported, opening separate windows..."
                        gnome-terminal --title="Database" -- bash -c "cd '$SCRIPTS_ROOT/docker/website-dev' && ENV=dev docker-compose up db; exec bash" 2>/dev/null &
                        sleep 0.5
                        gnome-terminal --title="Frontend" -- bash -c "cd '$SCRIPTS_ROOT/frontend' && ENV=dev npm install && npm run dev; exec bash" 2>/dev/null &
                        sleep 0.5
                        gnome-terminal --title="Backend" -- bash -c "cd '$SCRIPTS_ROOT/backend' && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash" 2>/dev/null &
                    }
                elif command -v konsole &> /dev/null; then
                    echo "Using konsole with tabs"
                    konsole \
                        --new-tab -p tabtitle="Database" -e bash -c "cd '$SCRIPTS_ROOT/docker/website-dev' && ENV=dev docker-compose up db; exec bash" \
                        --new-tab -p tabtitle="Frontend" -e bash -c "cd '$SCRIPTS_ROOT/frontend' && ENV=dev npm install && npm run dev; exec bash" \
                        --new-tab -p tabtitle="Backend" -e bash -c "cd '$SCRIPTS_ROOT/backend' && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash"
                elif command -v mate-terminal &> /dev/null; then
                    echo "Using mate-terminal with tabs"
                    mate-terminal \
                        --tab --title="Database" -e "bash -c 'cd \"$SCRIPTS_ROOT/docker/website-dev\" && ENV=dev docker-compose up db; exec bash'" \
                        --tab --title="Frontend" -e "bash -c 'cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev; exec bash'" \
                        --tab --title="Backend" -e "bash -c 'cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash'"
                elif command -v xfce4-terminal &> /dev/null; then
                    echo "Using xfce4-terminal with tabs"
                    xfce4-terminal \
                        --tab --title="Database" --command="bash -c 'cd \"$SCRIPTS_ROOT/docker/website-dev\" && ENV=dev docker-compose up db; exec bash'" \
                        --tab --title="Frontend" --command="bash -c 'cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev; exec bash'" \
                        --tab --title="Backend" --command="bash -c 'cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash'"
                elif command -v tilix &> /dev/null; then
                    echo "Using tilix with panes"
                    tilix -e "bash -c 'cd \"$SCRIPTS_ROOT/docker/website-dev\" && ENV=dev docker-compose up db; exec bash'" \
                          -a session-add-down -e "bash -c 'cd \"$SCRIPTS_ROOT/frontend\" && ENV=dev npm install && npm run dev; exec bash'" \
                          -a session-add-right -e "bash -c 'cd \"$SCRIPTS_ROOT/backend\" && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018; exec bash'"
                elif command -v terminator &> /dev/null; then
                    echo "Using terminator with splits"
                    terminator -l elanora_dev
                elif [[ "$OSTYPE" == "darwin"* ]]; then
                    echo "Using macOS Terminal with tabs"
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
                    echo "Running all services in current terminal with background processes..."
                    echo "Starting Database in background..."
                    (cd website/docker/website-dev && ENV=dev docker-compose up db) &
                    echo "Starting Frontend in background..."
                    (cd website/frontend && ENV=dev npm install && npm run dev) &
                    echo "Starting Backend in foreground..."
                    (cd website/backend && ENV=dev poetry install && poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8018)
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