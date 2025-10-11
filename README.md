# Alter Earth API

A sustainable community platform built with Python FastAPI, featuring AI-powered content curation and distributed architecture.

## 🌱 Project Overview

Alter Earth is a community platform focused on ecological conservation, green technology, and sustainable living. The platform leverages AI for content curation and promotes the mission of applying new technology to conservation and sustainability.

## 🛠 Tech Stack

- **Backend**: Python FastAPI
- **Database**: PostgreSQL (Supabase)
- **Authentication**: AWS Cognito
- **AI Integration**: Claude API
- **Background Jobs**: Celery/RQ
- **Infrastructure**: AWS EC2, Docker
- **Frontend**: Next.js (separate repository)

## 🏗 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI        │    │   Claude API    │
│   Frontend      │────│   API Server     │────│   Integration   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AWS Cognito   │    │   Background     │    │   News APIs     │
│   Auth          │    │   Workers        │    │   RSS Feeds     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (tested with Python 3.13)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/bsechel/alter-earth-api.git
   cd alter-earth-api
   ```

2. **Run the setup script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Start the development server**
   ```bash
   source venv/bin/activate
   uvicorn main:app --reload
   ```

### Manual Installation

If you prefer manual setup:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install fastapi uvicorn[standard]

# Start the server
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## 📚 Documentation

- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **OpenAPI Spec**: `docs/api/openapi-v1-phase2.json`
- **Frontend Integration**: See `docs/FRONTEND_INTEGRATION.md`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

