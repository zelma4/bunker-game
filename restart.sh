#!/bin/bash

echo "🛑 Stopping existing containers..."
docker compose down

echo "🏗️  Building and starting containers..."
docker compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 3

echo "📋 Container status:"
docker compose ps

echo ""
echo "✅ Ready! Access the game at: http://localhost"
echo ""
echo "📊 To view logs: docker compose logs -f"
echo "🛑 To stop: docker compose down"
