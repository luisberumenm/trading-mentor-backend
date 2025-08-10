import os
from fastapi import FastAPI, HTTPException
import httpx
import logging

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    metals_key = os.getenv("METALS_API_KEY")
    finnhub_key = os.getenv("FINNHUB_API_KEY")

    print(f"METALS_API_KEY: {metals_key}")
    print(f"FINNHUB_API_KEY: {finnhub_key}")

    if not metals_key or not finnhub_key:
        raise RuntimeError("API keys must be set in environment variables")

@app.get("/price/{symbol}")
async def get_price(symbol: str):
    symbol = symbol.upper()

    if symbol == "XAUUSD":
        metals_api_key = os.getenv("METALS_API_KEY")
        if not metals_api_key:
            raise HTTPException(status_code=500, detail="Metals API key not configured")

        # Use same URL and params as your local working code
        metals_url = "https://api.metals.dev/v1/latest"
        params = {
            "api_key": metals_api_key,
            "currency": "USD",
            "unit": "toz"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(metals_url, params=params)

        try:
            data = resp.json()
        except Exception as e:
            logging.error(f"Failed to parse JSON: {e}")
            raise HTTPException(status_code=502, detail="Invalid response from metals.dev API")

        # Check for the gold price key exactly like local code
        if 'metals' in data and 'gold' in data['metals']:
            price = data['metals']['gold']
            return {"symbol": symbol, "price": price, "raw_data": data}
        else:
            # Provide helpful error info
            return {"error": "Could not fetch gold price", "raw_data": data}

    else:
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        if not finnhub_key:
            raise HTTPException(status_code=500, detail="Finnhub API key not configured")

        finnhub_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={finnhub_key}"

        async with httpx.AsyncClient() as client:
            resp = await client.get(finnhub_url)

        data = resp.json()
        return {"symbol": symbol, "price_data": data}
