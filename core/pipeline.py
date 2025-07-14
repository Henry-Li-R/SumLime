from core.providers.deepseek import DeepSeekProvider
from core.providers.chatgpt import ChatGPTProvider
from core.providers.claude import ClaudeProvider
from core.providers.gemini import GeminiProvider

def verify_claim(claim: str) -> dict:
    """
    Verify a factual claim using multiple LLMs.

    Args:
        claim (str): A sentence or assertion to verify.

    Returns:
        dict: Structured output with verdict, summary, and model-wise details.
    """  
    
    
    ds = DeepSeekProvider()
    ds_results = ds.query(claim)

    gmn = GeminiProvider()
    gmn_results = gmn.query(claim)
    gmn_summarize = gmn.query(claim, system_message=gmn.SUMMARIZE_MESSAGE)
    '''
    cgpt = ChatGPTProvider()
    cgpt_results = cgpt.query(claim)

    cld = ClaudeProvider()
    cld_results = cld.query(claim)
    '''
    
    return { 
        "verdict": "uncertain", 
        "summary": "Verification not yet implemented.", 
        "details": [ds_results, gmn_results]
        }
