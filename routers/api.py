from fastapi import APIRouter,Query
from utility.utills import get_netflix_analysis

router = APIRouter()

@router.get("/news", summary="Get news and analysis for a given company")
async def get_news(company: str = Query(..., description="The company name to search news for")):
    """
    Fetch news articles for the provided company, extract webpage content, perform sentiment and topic analysis,
    and generate a comparative analysis.
    """
    analysis = get_netflix_analysis(company)
    return analysis
