# Deployment Guide

## Local Development

1. Install Python 3.8+
2. Create virtual environment: `python -m venv .venv`
3. Activate: `.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Set environment variables in `.env`
6. Run: `python backend/app.py`

## Production Deployment

- Use Gunicorn: `gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app`
- Set `FLASK_ENV=production`
- Use a reverse proxy like Nginx
- Secure API keys and sensitive data