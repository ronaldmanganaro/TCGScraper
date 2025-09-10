#!/bin/bash

# TCG Scraper - React + FastAPI Startup Script

echo "🧙 Starting TCG Scraper with React + FastAPI..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOL
# Database Configuration
DB_HOST=db
DB_PORT=5432
DB_NAME=tcgplayerdb
DB_USER=rmangana
DB_PASSWORD=password

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production-$(openssl rand -hex 32)
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API Configuration
VITE_API_BASE_URL=http://localhost:8000
EOL
    echo "✅ Created .env file with default configuration"
fi

# Start services
echo "🚀 Starting services with Docker Compose..."
docker-compose -f docker-compose.react-fastapi.yml up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Check if database initialization is needed
echo "🔍 Checking if database needs initialization..."
DB_EXISTS=$(docker exec tcgplayerdb psql -U rmangana -d tcgplayerdb -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='users';" 2>/dev/null)

if [ "$DB_EXISTS" != "1" ]; then
    echo "📊 Initializing database..."
    docker exec -i tcgplayerdb psql -U rmangana -d tcgplayerdb < api/init_db.sql
    echo "✅ Database initialized successfully"
else
    echo "✅ Database already initialized"
fi

echo ""
echo "🎉 TCG Scraper is now running!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 API Docs: http://localhost:8000/docs"
echo "🗄️  pgAdmin: http://localhost:80"
echo ""
echo "👤 Default login:"
echo "   Username: rmangana"
echo "   Password: admin123"
echo ""
echo "📋 To view logs: docker-compose -f docker-compose.react-fastapi.yml logs"
echo "🛑 To stop: docker-compose -f docker-compose.react-fastapi.yml down"
echo ""
echo "Happy scraping! 🧙‍♂️"
