import os
import logging
from tools.orchestrator_groq import run_groq_orchestrator, GroqOrchestratorError
from tools.orchestrator_fallback import run_fallback_orchestrator

# Setup logging for auditable execution (useful for debugging and judges)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Agentic-Orchestrator")

def run_smart_agent(user_query: str, uploaded_images: list[str]) -> str:
    """
    Master wrapper function. Attempts the Primary Groq path first.
    If it fails (or is simulated to fail), it seamlessly reroutes to the Offline Fallback path.
    """
    logger.info(f"Incoming Request - Query: '{user_query}', Images: {len(uploaded_images)}")
    
    # 1. Check for Simulation Flag
    simulate_failure = os.environ.get("SIMULATE_GROQ_FAILURE", "false").lower() == "true"
    
    if simulate_failure:
        logger.warning("SIMULATE_GROQ_FAILURE is TRUE. Bypassing Groq and forcing fallback path.")
        groq_failed = True
    else:
        # 2. Try Primary Path
        try:
            logger.info("Attempting Primary Path: Groq LLM Orchestrator...")
            final_response = run_groq_orchestrator(user_query, uploaded_images)
            logger.info("Primary Path Successful. Returning result.")
            return final_response
        except GroqOrchestratorError as e:
            logger.error(f"Primary Path Failed: {str(e)}")
            groq_failed = True

    # 3. Trigger Fallback Path (if Groq failed or was bypassed)
    if groq_failed:
        logger.info("Triggering Fallback Path: Offline BART-MNLI Zero-Shot Router...")
        fallback_response = run_fallback_orchestrator(user_query, uploaded_images)
        logger.info("Fallback Path Successful. Returning result.")
        return fallback_response
