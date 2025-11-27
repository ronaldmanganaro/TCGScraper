#!/bin/bash
set -e  # Exit on error

echo "Starting PostgreSQL..."
docker-entrypoint.sh postgres &  # Start PostgreSQL in the background

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h tcg-database-service -p 5432 -U postgres; do
  echo "PostgreSQL is not ready yet..."
  sleep 2
done

echo "Running database initialization script..."
python3 /initDB.py || { echo "Failed to run initDB.py"; exit 1; }

# Keep PostgreSQL running in the foreground
wait
