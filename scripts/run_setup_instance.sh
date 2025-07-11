#!/bin/bash
# Run the ELANORA instance setup wizard using Poetry from backend root
cd "$(dirname "$0")/../website/backend"
poetry run python ../../installer/setup_instance.py
if [ $? -ne 0 ]; then
    echo
    echo "Python script failed! Press Enter to see the error..."
    read
fi
echo
read -p "Script finished. Press Enter to exit..."