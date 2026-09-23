import logging
import os
import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from verdict_engine import run_verdict_engine

load_dotenv()

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    traces_sample_rate=1.0,
)

logger = logging.getLogger("suspicious_o_meter")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Suspicious-0-Meter API is running"}

@app.get("/ping")
def ping():
    return {"status": "ok"}

class ScanRequest(BaseModel):
    url: str
    text: str = Field(min_length=1, max_length=10000)

@app.post("/scan")
@limiter.limit("10/minute")
def scan_job(request: Request, job: ScanRequest):
    try:
        result = run_verdict_engine(job.text)
        return result
    except Exception as e:
        logger.exception("Internal error processing scan request")
        sentry_sdk.capture_exception(e)
        # Mask internal exception details to prevent information disclosure
        return {
            "suspicion_score": 0,
            "verdict": "ERROR",
            "error": "An internal error occurred while analyzing the posting."
        }