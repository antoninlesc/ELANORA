#!/bin/bash

cd "$(dirname "$0")/../.."

# Check Docker compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

check_docker() {
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
                check_docker || continue
                cd website/docker/website-dev
                export ENVIRONMENT=dev
                echo "Running: $COMPOSE_CMD up"
                $COMPOSE_CMD up
                if [ $? -ne 0 ]; then
                    echo ""
                    echo "ERROR: Docker compose failed!"
                    read -p "Press Enter to exit..."
                fi
                exit 0
            elif [[ "$USE_DOCKER" == "no" ]]; then
                check_docker || continue
                REPO_ROOT="$(pwd)/website"
                # Detect terminal type
                if command -v wezterm &> /dev/null && wezterm cli list >/dev/null 2>&1; then
                    # WezTerm - start new instance with 3 tabs, each renamed and running its component
                    pane_id1=$(wezterm cli spawn --new-window -- bash -c "printf '\e]2;ELANora - Database\a'; cd '$REPO_ROOT/docker/website-dev' && export ENVIRONMENT=dev && $COMPOSE_CMD up db; bash")
                    if [[ -z "$pane_id1" ]]; then
                        echo "Failed to spawn database pane."
                        continue
                    fi
                    wezterm cli set-tab-title --pane-id $pane_id1 "ELANora - Database"
                    # Get the window-id for the new window (parse tabular output: WINID is col 1, PANEID is col 3)
                    window_id=$(wezterm cli list | awk '$3 == '$pane_id1' {print $1}')
                    if [[ -z "$window_id" ]]; then
                        echo "Failed to retrieve window_id."
                        continue
                    fi
                    pane_id2=$(wezterm cli spawn --window-id $window_id -- bash -c "printf '\e]2;ELANora - Frontend\a'; cd '$REPO_ROOT/frontend' && export ENVIRONMENT=dev && npm install && (npm audit fix || echo 'Audit fix failed, continuing...') && npm run dev; bash")
                    if [[ -n "$pane_id2" ]]; then
                        wezterm cli set-tab-title --pane-id $pane_id2 "ELANora - Frontend"
                    fi
                    pane_id3=$(wezterm cli spawn --window-id $window_id -- bash -c "printf '\e]2;ELANora - Backend\a'; cd '$REPO_ROOT/backend' && export ENVIRONMENT=dev && poetry install && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8018; bash")
                    if [[ -n "$pane_id3" ]]; then
                        wezterm cli set-tab-title --pane-id $pane_id3 "ELANora - Backend"
                    fi
                    echo "New WezTerm window launched with tabs: ELANora - Database, ELANora - Frontend, ELANora - Backend."
                    exit 0
                elif command -v gnome-terminal &> /dev/null; then
                    # GNOME Terminal - open 3 separate windows
                    gnome-terminal --window -- bash -c "cd '$REPO_ROOT/docker/website-dev' && export ENVIRONMENT=dev && $COMPOSE_CMD up db; bash" &
                    gnome-terminal --window -- bash -c "cd '$REPO_ROOT/frontend' && export ENVIRONMENT=dev && npm install && (npm audit fix || echo 'Audit fix failed, continuing...') && npm run dev; bash" &
                    gnome-terminal --window -- bash -c "cd '$REPO_ROOT/backend' && export ENVIRONMENT=dev && poetry install && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8018; bash" &
                else
                    # Fallback to separate windows with x-terminal-emulator
                    x-terminal-emulator -T "Database" -e bash -c "cd '$REPO_ROOT/docker/website-dev' && export ENVIRONMENT=dev && $COMPOSE_CMD up db; bash" &
                    x-terminal-emulator -T "Frontend" -e bash -c "cd '$REPO_ROOT/frontend' && export ENVIRONMENT=dev && npm install && (npm audit fix || echo 'Audit fix failed, continuing...') && npm run dev; bash" &
                    x-terminal-emulator -T "Backend" -e bash -c "cd '$REPO_ROOT/backend' && export ENVIRONMENT=dev && poetry install && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8018; bash" &
                fi
                # Removed exit 0 to keep the initial WezTerm window open
                break
            elif [[ "$USE_DOCKER" == "back" ]]; then
                break
            else
                echo "Invalid choice. Please enter 'yes', 'no', or 'back'."
            fi
        done
    elif [[ "$ENV" == "prod" ]]; then
        check_docker || continue
        cd website/docker/website-prod
        export ENVIRONMENT=prod
        echo "Running: $COMPOSE_CMD up"
        $COMPOSE_CMD up
        if [ $? -ne 0 ]; then
            echo ""
            echo "ERROR: Docker compose failed!"
            read -p "Press Enter to exit..."
        fi
        exit 0
    elif [[ "$ENV" == "server" ]]; then
        check_docker || continue
        cd website/docker/website-server
        export ENVIRONMENT=server
        echo "Running: $COMPOSE_CMD up"
        $COMPOSE_CMD up
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