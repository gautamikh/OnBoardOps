from fastapi import FastAPI

app = FastAPI(
    title="OnboardOps API",
    description="AI-assisted employee onboarding",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "onboardops-api"}