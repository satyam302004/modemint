# ModeMint - AI Fashion Outfit Recommender

A Flask-based web application that provides AI-powered outfit recommendations using fashion trends, wardrobe items, and product catalogs.

## Features

- Outfit recommendations based on occasion, style, and budget
- Wardrobe management with image upload and AI detection
- Chat interface for personalized styling advice
- Trend analysis and integration
- Favorites system for saving outfits

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate: `.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment variables in `.env`
6. Run the app: `python backend/app.py`

## API Endpoints

- `GET /` - Health check
- `GET /products` - Get product catalog
- `POST /recommend` - Get outfit recommendations
- `GET /wardrobe` - Get wardrobe items
- `POST /wardrobe` - Add wardrobe item
- `POST /chat` - AI chat for styling advice

## Project Structure

- `backend/` - Flask API server
- `frontend/` - Web interface
- `scripts/` - Utility scripts
- `docs/` - Documentation