from fastapi import FastAPI, HTTPException
import os
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

        metals_url = "https://metals.dev/api/latest"
        headers = {
            "x-api-key": metals_api_key
        }
        params = {
            "base": "USD",
            "symbols": "XAU"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(metals_url, headers=headers, params=params)
        data = resp.json()

        if not data.get("success", False):
            error_info = data.get("error", {}).get("info", "Unknown error")
            raise HTTPException(status_code=502, detail=f"Error fetching metals data: {error_info}")

        return {"raw_metals_api_response": data}

    else:
        finnhub_api_key = os.getenv("FINNHUB_API_KEY")
        if not finnhub_api_key:
            raise HTTPException(status_code=500, detail="Finnhub API key not configured")

        finnhub_url = "https://finnhub.io/api/v1/quote"
        params = {
            "symbol": symbol,
            "token": finnhub_api_key
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
