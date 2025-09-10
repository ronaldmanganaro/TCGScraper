# TCG Scraper - React + FastAPI Migration

This document explains the new React frontend + FastAPI backend architecture for the TCG Scraper application.

## Architecture Overview

The application has been migrated from Streamlit to a modern web stack:

- **Frontend**: React with TypeScript, Material-UI, and Vite
- **Backend**: FastAPI with async/await support
- **Database**: PostgreSQL
- **Authentication**: JWT tokens with bcrypt password hashing
- **Containerization**: Docker and Docker Compose

## Project Structure

```
TCGPyScraper/
├── api/                          # FastAPI backend
│   ├── main.py                   # Main FastAPI application
│   ├── models/
│   │   └── schemas.py            # Pydantic models
│   ├── services/                 # Business logic services
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── repricer.py
│   │   ├── ev_tools.py
│   │   └── ...
│   ├── requirements.txt
│   ├── Dockerfile
│   └── init_db.sql
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── components/           # Reusable components
│   │   ├── pages/                # Page components
│   │   ├── services/             # API client
│   │   ├── contexts/             # React contexts
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.react-fastapi.yml
└── README-React-FastAPI.md
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd TCGPyScraper
   ```

2. **Start all services**
   ```bash
   docker-compose -f docker-compose.react-fastapi.yml up -d
   ```

3. **Initialize the database** (first time only)
   ```bash
   docker exec -i tcgplayerdb psql -U rmangana -d tcgplayerdb < api/init_db.sql
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - pgAdmin: http://localhost:80

### Local Development

#### Backend Development

1. **Set up Python environment**
   ```bash
   cd api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set environment variables**
   ```bash
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_NAME=tcgplayerdb
   export DB_USER=rmangana
   export DB_PASSWORD=password
   export JWT_SECRET_KEY=your-secret-key-change-in-production
   ```

3. **Run the FastAPI server**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

#### Frontend Development

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**
   ```bash
   npm run dev
   ```

The frontend will be available at http://localhost:3000 with hot reload enabled.

## Features

### Authentication System
- JWT-based authentication
- User registration and login
- Admin-only routes and features
- Secure password hashing with bcrypt

### Core Functionality
- **Repricer**: Upload inventory CSVs, filter data, update prices
- **EV Tools**: Simulate booster box openings, calculate precon EV
- **Pokemon Tracker**: Track Pokemon card prices
- **Manabox Converter**: Convert ManaBox CSV files
- **Inventory Management**: View and manage card collections
- **TCGPlayer Orders**: Extract and process order PDFs

### API Endpoints

The FastAPI backend provides RESTful endpoints:

- `POST /auth/login` - User authentication
- `GET /auth/me` - Get current user info
- `POST /repricer/upload` - Upload inventory CSV
- `POST /repricer/filter` - Filter inventory data
- `POST /ev-tools/simulate-box` - Simulate booster box
- `GET /pokemon/prices` - Get Pokemon prices
- And many more...

Full API documentation is available at http://localhost:8000/docs

## Database Schema

The PostgreSQL database includes tables for:
- `users` - User accounts and authentication
- `cards` - Card information and metadata
- `sets` - TCG set information
- `inventory` - User inventory items
- `price_history` - Historical price data
- `price_alerts` - Price alert configurations

## Migration from Streamlit

### Key Changes
1. **State Management**: Moved from Streamlit session state to React state and React Query
2. **File Handling**: Changed from Streamlit file uploads to multipart form data
3. **Authentication**: Implemented JWT-based auth instead of session-based
4. **Data Flow**: API-first architecture with proper separation of concerns
5. **UI Framework**: Material-UI components instead of Streamlit widgets

### Benefits
- **Performance**: Much faster loading and interactions
- **Scalability**: Proper separation allows independent scaling
- **Mobile Support**: Responsive design works on all devices
- **Developer Experience**: Modern tooling with hot reload
- **API Access**: RESTful API can be used by other applications

## Environment Variables

### Backend (.env)
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tcgplayerdb
DB_USER=rmangana
DB_PASSWORD=password
JWT_SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Frontend (.env)
```
VITE_API_BASE_URL=http://localhost:8000
```

## Production Deployment

For production deployment:

1. **Update environment variables** with secure values
2. **Use HTTPS** for both frontend and backend
3. **Configure reverse proxy** (nginx/traefik)
4. **Set up proper database backup**
5. **Enable logging and monitoring**

Example production docker-compose configuration would include:
- SSL certificates
- Production database configuration
- Health checks
- Restart policies
- Resource limits

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running
   - Check connection parameters
   - Verify database exists

2. **CORS Issues**
   - Check CORS configuration in FastAPI
   - Ensure frontend URL is in allowed origins

3. **Authentication Issues**
   - Verify JWT secret key is set
   - Check token expiration
   - Ensure user exists in database

4. **File Upload Issues**
   - Check file size limits
   - Verify multipart form data handling
   - Ensure proper file permissions

### Logs

View logs for debugging:
```bash
# All services
docker-compose -f docker-compose.react-fastapi.yml logs

# Specific service
docker-compose -f docker-compose.react-fastapi.yml logs api
docker-compose -f docker-compose.react-fastapi.yml logs frontend
```

## Contributing

When contributing to the React + FastAPI version:

1. **Backend Changes**: Add/modify FastAPI endpoints in `api/`
2. **Frontend Changes**: Update React components in `frontend/src/`
3. **Database Changes**: Update schema in `api/init_db.sql`
4. **API Client**: Update service functions in `frontend/src/services/api.ts`

## Testing

### Backend Testing
```bash
cd api
pytest
```

### Frontend Testing
```bash
cd frontend
npm test
```

## Future Enhancements

- [ ] Real-time price updates with WebSockets
- [ ] Advanced filtering and search
- [ ] Data visualization with charts
- [ ] Mobile app with React Native
- [ ] API rate limiting and caching
- [ ] Advanced admin dashboard
- [ ] Automated testing pipeline
