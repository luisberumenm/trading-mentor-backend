from fastapi import FastAPI, HTTPException
import os
import httpx

app = FastAPI()

# Load API keys globally once on app start
METALS_API_KEY = os.getenv("METALSDEV_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

if not METALS_API_KEY or not FINNHUB_API_KEY:
    raise RuntimeError("API keys must be set in environment variables")

@app.get("/")
async def root():
    return {"message": "API is working!"}

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
        if data.get("success"):
            price = data["rates"]["XAU"]
            return {
                "symbol": symbol,
                "price": price,
                "raw_data": data
            }
        else:
            raise HTTPException(status_code=502, detail="Error fetching metals data")

    else:
        finnhub_url = f"https://finnhub.io/api/v1/quote"
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
