import logging
import sentry_sdk
import os
from fastapi import FastAPI, Request, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    traces_sample_rate=1.0,
)

from verdict_engine import run_verdict_engine

logger = logging.getLogger("suspicious_o_meter")
logging.basicConfig(level=logging.INFO)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Suspicious-o-meter API",
    description="Backend scam analysis engine for job postings and communications",
    version="1.1.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
# Restricts cross-origin requests to local development and Chrome extension contexts
# Prevents arbitrary public websites from abusing the local scanning API
env_origins = os.environ.get("ALLOWED_ORIGINS")
if env_origins:
    allowed_origins = [o.strip() for o in env_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^(chrome-extension://.*|http://(localhost|127\.0\.0\.1)(:\d+)?)$",
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

# Optional API Key Authentication
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.environ.get("API_SECRET_KEY")
    if expected_key:
        if not api_key or api_key != expected_key:
            raise HTTPException(status_code=403, detail="Invalid or missing API Key")
    return api_key

@app.get("/")
def read_root():
    return {"message": "Suspicious-o-meter API is running", "version": "1.1.0"}

@app.get("/ping")
def ping():
    return {"status": "ok"}

class ScanRequest(BaseModel):
    url: str = Field(default="", max_length=2048)
    text: str = Field(min_length=1, max_length=20000)

@app.post("/scan")
@limiter.limit("10/minute")
def scan_job(request: Request, job: ScanRequest, _auth: str = Depends(verify_api_key)):
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