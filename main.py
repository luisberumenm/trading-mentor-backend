from fastapi import FastAPI, HTTPException
import os
import httpx

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    metals_key = os.getenv("METALSDEV_API_KEY")
    finnhub_key = os.getenv("FINNHUB_API_KEY")

    print(f"METALS_API_KEY: {metals_key}")
    print(f"FINNHUB_API_KEY: {finnhub_key}")

    if not metals_key or not finnhub_key:
        raise RuntimeError("API keys must be set in environment variables")

METALS_API_KEY = os.getenv("METALSDEV_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

@app.get("/price/{symbol}")
async def get_price(symbol: str):
    symbol = symbol.upper()

    if symbol == "XAUUSD":
        metals_url = "https://metals-api.com/api/latest"
        params = {
            "access_key": METALS_API_KEY,
            "base": "USD",
            "symbols": "XAU"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(metals_url, params=params)
        data = resp.json()
        # Return the full raw response from Metals API for debugging
        return {"raw_metals_api_response": data}

    else:
        finnhub_url = "https://finnhub.io/api/v1/quote"
        params = {
            "symbol": symbol,
            "token": FINNHUB_API_KEY
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(finnhub_url, params=params)
        data = resp.json()
        if data and "c" in data:
            return {
                "symbol": symbol,
                "price_data": data
            }
        else:
            raise HTTPException(status_code=502, detail="Error fetching stock data")
