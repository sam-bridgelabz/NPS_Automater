from fastapi import FastAPI
from routers.extract_reviews import review_router  # Import the new router

app = FastAPI(
    title="Review Extraction API",
    description="An API to extract reviews from Google Sheets and process them.",
    version="1.0.0"
)

# Include the router
app.include_router(review_router)
