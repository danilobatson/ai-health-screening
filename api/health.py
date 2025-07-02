from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {
        "status": "healthy", 
        "service": "AI Healthcare Backend",
        "platform": "Vercel Serverless"
    }

def handler(request, response):
    return app(request, response)
