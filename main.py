import os
from fastapi import FastAPI, HTTPException
import httpx
import logging
from datetime import datetime

app = FastAPI()

# Whitelist of 50 most commonly traded US stocks (large-cap, liquid)
ALLOWED_STOCKS = {
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "BRK.B", "JPM", "JNJ",
    "V", "PG", "DIS", "MA", "HD", "PYPL", "BAC", "ADBE", "CMCSA", "NFLX",
    "XOM", "KO", "CSCO", "PFE", "MRK", "INTC", "T", "VZ", "CVX", "WMT",
    "ABT", "PEP", "CRM", "ACN", "NKE", "ORCL", "COST", "TXN", "MDT", "QCOM",
    "LLY", "DHR", "BMY", "NEE", "UPS", "IBM", "LIN", "HON", "MMM", "GE"
}

def mask_key(key: str) -> str:
    if not key or len(key) < 6:
        return "***"
    return key[:3] + "***" + key[-3:]

@app.on_event("startup")
async def startup_event():
    metals_key = os.getenv("METALS_API_KEY")
    finnhub_key = os.getenv("FINNHUB_API_KEY")

    # Mask keys in logs for safety
    logging.info(f"METALS_API_KEY present: {bool(metals_key)}, value: {mask_key(metals_key)}")
    logging.info(f"FINNHUB_API_KEY present: {bool(finnhub_key)}, value: {mask_key(finnhub_key)}")

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
            logging.error(f"Failed to parse JSON from metals.dev API: {e}")
            raise HTTPException(status_code=502, detail="Invalid response from metals.dev API")

        if 'metals' in data and 'gold' in data['metals']:
            price = data['metals']['gold']
            timestamp = data.get('timestamp', datetime.utcnow().isoformat())
            return {
                "symbol": symbol,
                "price": price,
                "timestamp": timestamp,
                "source": "metals.dev"
            }
        else:
            logging.error(f"Gold price missing in metals.dev response: {data}")
            raise HTTPException(status_code=502, detail="Gold price not found in metals.dev API response")

    else:
        # Validate stock symbol whitelist
        if ALLOWED_STOCKS and symbol not in ALLOWED_STOCKS:
            raise HTTPException(status_code=400, detail=f"Stock symbol '{symbol}' is not allowed or supported")

        finnhub_key = os.getenv("FINNHUB_API_KEY")
        if not finnhub_key:
            raise HTTPException(status_code=500, detail="Finnhub API key not configured")

        finnhub_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={finnhub_key}"

        async with httpx.AsyncClient() as client:
            resp = await client.get(finnhub_url)

        if resp.status_code != 200:
            logging.error(f"Finnhub API error: {resp.status_code} {resp.text}")
            raise HTTPException(status_code=502, detail="Error fetching stock data from Finnhub")

        data = resp.json()

        # Check for valid price data (Finnhub returns c=0 if symbol invalid)
        if "c" not in data or data["c"] == 0:
            raise HTTPException(status_code=404, detail=f"No valid price data found for symbol '{symbol}'")

        return {
            "symbol": symbol,
            "price": data["c"],           # current price
            "high": data.get("h"),        # high price of the day
            "low": data.get("l"),         # low price of the day
            "open": data.get("o"),        # open price
            "previous_close": data.get("pc"),
            "timestamp": datetime.utcfromtimestamp(data.get("t", datetime.utcnow().timestamp())).isoformat(),
            "source": "Finnhub"
        }
