# Setup Guide

This guide will help you set up the Airline Market Demand application locally for development and testing purposes.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend development)
- Git

## 1. Clone the Repository

```bash
git clone https://github.com/yourusername/airline-market-demand.git
cd airline-market-demand
```

## 2. Set Up Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your configuration:
   ```bash
   # Database
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=airline_market
   DATABASE_URL=postgresql://postgres:postgres@db:5432/airline_market
   
   # API Keys (get these from the respective providers)
   AMADEUS_CLIENT_ID=your_amadeus_client_id
   AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
   RAPIDAPI_KEY=your_rapidapi_key
   AVIATIONSTACK_API_KEY=your_aviationstack_api_key
   GROQ_API_KEY=your_groq_api_key
   
   # App Settings
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

## 3. Start the Development Environment

Run the following command to start all services:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- PgAdmin (available at http://localhost:5050)
- FastAPI backend (available at http://localhost:8000)
- Frontend development server (available at http://localhost:3000)

## 4. Run Database Migrations

```bash
docker-compose exec web alembic upgrade head
```

## 5. Access the Application

- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- PgAdmin: http://localhost:5050
  - Email: admin@example.com
  - Password: admin

## Development Workflow

### Backend Development

To run the backend server in development mode:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The server will be available at http://localhost:8000

### Frontend Development

To run the frontend development server:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

## Testing

### Backend Tests

```bash
docker-compose exec web pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Production Deployment

### Building for Production

1. Build the Docker images:
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```

2. Start the production services:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Environment Variables for Production

Make sure to update these environment variables in production:

```
APP_ENV=production
DEBUG=False
SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgresql://username:password@db:5432/airline_market_prod
```

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:

1. Verify that PostgreSQL is running:
   ```bash
   docker-compose ps
   ```

2. Check the database logs:
   ```bash
   docker-compose logs db
   ```

### Port Conflicts

If you get port conflicts, you can change the ports in the `docker-compose.yml` file:

```yaml
services:
  web:
    ports:
      - "8001:8000"  # Change the first port number
  
  frontend:
    ports:
      - "3001:3000"  # Change the first port number
  
  db:
    ports:
      - "5433:5432"  # Change the first port number
  
  pgadmin:
    ports:
      - "5051:80"    # Change the first port number
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
