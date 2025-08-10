import os
import logging
from fastapi import FastAPI, HTTPException
import httpx

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

        metals_url = "https://api.metals.dev/v1/latest"
        headers = {"x-api-key": metals_api_key}
        params = {
            "base": "USD",
            "symbols": "XAU"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(metals_url, params=params, headers=headers)

        content = resp.text
        logging.info(f"Raw metals.dev response content: {content}")

        try:
            data = resp.json()
        except Exception as e:
            logging.error(f"Failed to parse JSON: {e}")
            raise HTTPException(status_code=502, detail="Invalid response from metals.dev API")

        if not data.get("success", False):
            error_info = data.get("error", {}).get("info", "Unknown error")
            raise HTTPException(status_code=502, detail=f"Error fetching metals data: {error_info}")

        return {"raw_metals_api_response": data}

    else:
        # Your existing Finnhub or other symbol handling here
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        if not finnhub_key:
            raise HTTPException(status_code=500, detail="Finnhub API key not configured")

        finnhub_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}"
        params = {"token": finnhub_key}

        async with httpx.AsyncClient() as client:
            resp = await client.get(finnhub_url, params=params)
        
        data = resp.json()
        return {"raw_finnhub_response": data}
