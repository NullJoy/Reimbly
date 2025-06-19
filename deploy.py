from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from reimbly.root_agent import root_agent
import os

app = FastAPI(title="Reimbly ADK Deployment")

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <h1>Reimbly ADK API</h1>
    <p>Welcome! The root agent is ready. POST to <code>/agent</code> to interact.</p>
    """

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/agent")
async def interact_agent(request: Request):
    data = await request.json()
    user_input = data.get("input", "")
    # Call the root agent (adapt as needed for your ADK version)
    response = root_agent(user_input)
    return JSONResponse(content={"response": response})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("deploy:app", host="0.0.0.0", port=port)
