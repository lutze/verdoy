import httpx
from fastapi import FastAPI
from sqlalchemy import create_engine

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


# Configure the database connection string
DATABASE_URL = "postgresql://postgres:password@db:5432/myapp"
engine = create_engine(DATABASE_URL)

@app.get("/db-check")
async def check_db():
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT version();")
            version = result.fetchone()[0]
        return {"status": "success", "postgres_version": version}
    except Exception as e:
        return {"status": "error", "message": str(e)}



@app.post("/ollama-check")
async def ollama_check():
    # Define the payload for the external API
    payload = {
        "model": "llama3.1",
        "prompt": "What's a single word for a thing that holds a chemical solution? Respond with the answer in a single JSON object like {answer:''}",
        "stream": False
    }

    # Define the headers
    headers = {
        "Content-Type": "application/json"
    }

    # Make the POST request
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://localhost:11434/api/generate", json=payload, headers=headers)

        # Return the response from the external API
        return {"status": "success", "data": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}
