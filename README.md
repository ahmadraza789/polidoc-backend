# PoliDoc Backend

A FastAPI-based backend service for PoliDoc, providing API endpoints for insurance policy document management and analysis.

## Features

- Neo4j Graph Database Integration
- FastAPI REST API
- Policy Document Analysis
- Form Management

## Setup

1. Clone the repository:
```bash
git clone https://github.com/ahmadraza789/polidoc-backend.git
cd polidoc-backend
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Set up environment variables in `.env`:
```env
NEO4J_URI=your_neo4j_uri
NEO4J_USER=your_neo4j_user
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j
```

4. Run the server:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Graph API

- `GET /api/v1/graph/test-connection`: Test Neo4j connection
- `GET /api/v1/graph/forms`: Get list of forms
- `GET /api/v1/graph/policy-types`: Get list of policy types

## Development

- Python 3.12+
- FastAPI
- Neo4j
- Loguru for logging

## License

MIT License 