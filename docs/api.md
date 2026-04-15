# API Documentation

## Endpoints

### GET /
Health check endpoint.

**Response:**
```
"AI Outfit Recommendation API is running."
```

### GET /meta
Get available options for occasions, styles, and budgets.

**Response:**
```json
{
  "occasions": ["wedding", "casual", "party", "college", "formal"],
  "styles": ["minimal", "streetwear", "ethnic", "classic", "chic", "smart-casual"],
  "budgets": [2000, 5000, 10000]
}
```

### GET /products
Get the product catalog.

**Response:** Array of product objects.

### GET /trends
Get fashion trends data.

**Response:** Array of trend objects.

### POST /recommend
Get outfit recommendations.

**Request Body:**
```json
{
  "occasion": "casual",
  "style": "minimal",
  "budget": 5000
}
```

**Response:** Outfit recommendations with query details.

### GET /favorites
Get saved favorite outfits.

### POST /favorites
Save an outfit to favorites.

### DELETE /favorites/{id}
Delete a favorite outfit.

### GET /wardrobe
Get wardrobe items.

### POST /wardrobe
Add a wardrobe item.

### POST /wardrobe/upload
Upload an image to analyze for wardrobe.

### DELETE /wardrobe/{id}
Delete a wardrobe item.

### POST /wardrobe/generate
Generate outfits from wardrobe.

### POST /chat
Chat with AI stylist.

**Request Body:**
```json
{
  "message": "Suggest a casual outfit under 5000"
}
```

**Response:** AI response text.