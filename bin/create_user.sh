#!/bin/bash
# AEGIS_IDENTITY: Create a new SC-ARCHIVE user
# Usage: ./bin/create_user.sh <username> <password>

set -e

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./bin/create_user.sh <username> <password>"
    exit 1
fi

cd "$(dirname "$0")/.."

poetry run python -c "
from logic.auth import auth_service
auth_service.create_user_sync('$1', '$2')
print('USER_CREATED // $1 -> workspace: ~/sc-archive/$1')
"
