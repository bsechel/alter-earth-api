# Alter Earth API

A sustainable community platform built with Python FastAPI, featuring AI-powered content curation and distributed architecture.

## 🌱 Project Overview

Alter Earth is a Reddit-like community platform focused on ecological conservation, green technology, and sustainable living. The platform leverages AI for intelligent content curation and demonstrates modern platform engineering practices.

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

