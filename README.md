# Airline Market Demand Analysis

A web application for analyzing airline booking market demand trends, built with FastAPI, React, and PostgreSQL.

## Features

- **Data Collection**: Fetches airline booking data from multiple sources with automatic fallback to mock data
- **Data Analysis**: Processes and analyzes market trends, pricing, and demand patterns
- **Interactive Dashboard**: Visualizes data with interactive charts and tables
- **API Integration**: Connects with Amadeus, RapidAPI, and AviationStack APIs
- **Scalable Architecture**: Built with microservices in mind, containerized with Docker

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Alembic
- **Frontend**: React, TypeScript, Chart.js, TailwindCSS
- **Database**: PostgreSQL
- **Infrastructure**: Docker, Docker Compose, Vercel (for deployment)
- **APIs**: Amadeus, RapidAPI, AviationStack

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend development)
- API keys for Amadeus, RapidAPI, and AviationStack (optional)

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/airline-market-demand.git
cd airline-market-demand
```

### 2. Set up environment variables

Copy the example environment file and update it with your configuration:

```bash
cp .env.example .env
```

Edit the `.env` file with your database credentials and API keys.

### 3. Start the development environment

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- PgAdmin (available at http://localhost:5050)
- FastAPI backend (available at http://localhost:8000)
- Frontend development server (available at http://localhost:3000)

### 4. Run database migrations

```bash
docker-compose exec web alembic upgrade head
```

### 5. Access the application

- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- PgAdmin: http://localhost:5050

## Development

### Backend Development

To run the backend server in development mode:

```bash
cd backend
uvicorn app.main:app --reload
```

### Frontend Development

To run the frontend development server:

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Run backend tests
docker-compose exec web pytest

# Run frontend tests
cd frontend
npm test
```

## Production Deployment

### Building for Production

```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

For production, make sure to set the following environment variables:

```
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

## API Documentation

API documentation is available at `/docs` when running the application locally.

## License

This project is unlicensed - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request