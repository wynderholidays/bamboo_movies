#!/usr/bin/env python3
import uvicorn
from main import app

if __name__ == "__main__":
    print("Starting Movie Booking API server...")
    print("API Documentation: http://localhost:8000/docs")
    print("API Base URL: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    uvicorn.run(app, host="0.0.0.0", port=8000)