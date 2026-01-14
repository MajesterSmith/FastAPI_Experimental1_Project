#!/bin/bash

# Docker migration helper script

case "$1" in
    "upgrade")
        echo "Running database migrations..."
        docker-compose exec app alembic upgrade head
        ;;
    "revision")
        shift
        message="$*"
        if [ -z "$message" ]; then
            echo "Usage: ./docker-migrate.sh revision \"migration message\""
            exit 1
        fi
        echo "Creating new migration: $message"
        docker-compose exec app alembic revision --autogenerate -m "$message"
        ;;
    "current")
        echo "Checking current migration status..."
        docker-compose exec app alembic current
        ;;
    "downgrade")
        echo "Rolling back last migration..."
        docker-compose exec app alembic downgrade -1
        ;;
    *)
        echo "Usage: $0 {upgrade|revision|current|downgrade}"
        echo ""
        echo "Commands:"
        echo "  upgrade     - Apply all pending migrations"
        echo "  revision    - Create a new migration (requires message)"
        echo "  current     - Show current migration status"
        echo "  downgrade   - Rollback last migration"
        exit 1
        ;;
esac