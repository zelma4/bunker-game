#!/bin/bash

echo "🔄 Applying database migrations..."

# Check if database is running
docker compose ps db | grep -q "Up"
if [ $? -ne 0 ]; then
    echo "❌ Database is not running. Start it with: docker compose up -d db"
    exit 1
fi

# Apply SQL migration
echo "📝 Adding special_data column to players table..."
docker compose exec -T db psql -U bunker <<EOF
ALTER TABLE players ADD COLUMN IF NOT EXISTS special_data JSONB;
CREATE INDEX IF NOT EXISTS idx_players_special_data ON players USING GIN (special_data);
EOF

if [ $? -eq 0 ]; then
    echo "✅ Migration applied successfully!"
else
    echo "❌ Migration failed!"
    exit 1
fi

echo ""
echo "🔍 Verifying column exists..."
docker compose exec -T db psql -U bunker -c "\d players" | grep "special_data"

if [ $? -eq 0 ]; then
    echo "✅ Column verified!"
else
    echo "⚠️  Could not verify column (may still be OK)"
fi
