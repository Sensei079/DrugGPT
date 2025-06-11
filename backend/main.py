from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fda_api import get_fda_data, check_drug_interaction, extract_drugs_from_query, normalize_drug_name
import logging
from typing import List
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app = FastAPI(
    title="Drug Interaction API",
    description="API for checking drug information and interactions using FDA data",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "https://druggpt.netlify.app"  # Add your Netlify URL here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DrugQuery(BaseModel):
    query: str
    query_type: str = "interaction"  # Can be "interaction" or "side_effects"

class DrugInfo(BaseModel):
    name: str
    info: str
    side_effects: str
    warnings: str
    is_safe: bool

class DrugResponse(BaseModel):
    drugs: List[DrugInfo]
    safe: bool
    interaction_message: str
    friendly_response: str

def generate_friendly_response(drugs: List[DrugInfo], is_safe: bool, interaction_message: str, query: str) -> str:
    """Generate a friendly, conversational response about the drug interaction or side effects."""
    if len(drugs) == 1:
        drug = drugs[0]
        if is_safe:
            return f"Based on FDA information, {drug['name']} appears to be safe to use. {drug['info']}"
        else:
            return f"⚠️ Caution: {drug['name']} has some important warnings. {drug['warnings']}"
    else:
        drug_names = ", ".join(d['name'] for d in drugs)
        if is_safe:
            return f"Good news! Based on our analysis, it appears safe to take {drug_names} together. {interaction_message}"
        else:
            return f"⚠️ Important: We've identified potential risks when taking {drug_names} together. {interaction_message}"

def normalize_drug_names(drugs: List[str]) -> List[str]:
    """Normalize drug names to prevent duplicates"""
    normalized = set()
    for drug in drugs:
        normalized_name = normalize_drug_name(drug)
        if normalized_name not in normalized:
            normalized.add(normalized_name)
    return list(normalized)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Drug Interaction API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints": {
            "check_interactions": "/check-interactions (POST)"
        }
    }

@app.post("/check-interactions", response_model=DrugResponse)
async def check_drug_interactions_endpoint(query: DrugQuery):
    try:
        logger.info(f"Received query: {query.query}")
        
        # Extract drugs from the natural language query
        drugs = extract_drugs_from_query(query.query)
        if not drugs:
            raise HTTPException(status_code=400, detail="No drugs found in the query")
        
        # Normalize drug names to prevent duplicates
        drugs = normalize_drug_names(drugs)
        logger.info(f"Extracted drugs: {drugs}")
        
        results = []
        
        # Get drug info from FDA API
        for drug in drugs:
            logger.info(f"Fetching data for drug: {drug}")
            drug_info = get_fda_data(drug)
            if drug_info:
                results.append(drug_info)
        
        # Check for interactions between drugs
        is_safe, interaction_message = check_drug_interaction(drugs)
        
        # Generate friendly response
        friendly_response = generate_friendly_response(results, is_safe, interaction_message, query.query)
        
        logger.info(f"Returning results for {len(results)} drugs")
        return {
            "drugs": results,
            "safe": is_safe,
            "interaction_message": interaction_message,
            "friendly_response": friendly_response
        }
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)