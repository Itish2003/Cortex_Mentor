from fastapi import FastAPI

app = FastAPI(
   title="Cortex Mentor Framework",
   version="0.1.0",
   description="The backend server for the agentic framework"
)

@app.get("/health",tags=["Health Check"])
def health_check_endpoint():
	"""A simple healthcheck endpoint"""
	return {"status":"ok","message":"health check passed..."}
