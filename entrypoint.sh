#!/bin/sh
# entrypoint.sh

echo "Pushing database schema..."
npx prisma db push

echo "Seeding database..."
npx prisma db seed

echo "Starting Next.js..."
exec "$@"
