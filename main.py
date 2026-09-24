import logging
import os
import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from verdict_engine import run_verdict_engine

load_dotenv()


def scrub_event(event, hint):
    # Strip request bodies so email/posting text never reaches Sentry
    event.get("request", {}).pop("data", None)
    return event


sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    traces_sample_rate=1.0,
    send_default_pii=False,
    include_local_variables=False,  # frame variables would contain the posting text
    before_send=scrub_event,
    before_send_transaction=scrub_event,
)

logger = logging.getLogger("suspicious_o_meter")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
# Return a clean 429 when the rate limit is hit, instead of a 500
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: only allow Chrome extensions and localhost by default.
# Optionally add more origins via the ALLOWED_ORIGINS env var (comma-separated).
extra_origins = [
    o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=extra_origins,
    allow_origin_regex=r"^(chrome-extension://[a-p]{32}|http://(localhost|127\.0\.0\.1)(:\d+)?)$",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
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