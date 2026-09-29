from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
)

from pydantic import BaseModel, Field

from ..services.recommendation_service import (
    RecommendationService
)


router = APIRouter(
    prefix="/api",
    tags=["Recommendations"]
)


recommendation_service = (
    RecommendationService()
)


# ============================================================
# TEXT RECOMMENDATION REQUEST
# ============================================================

class RecommendationRequest(
    BaseModel
):

    query: str = Field(
        ...,
        min_length=1
    )

    top_k: int = Field(
        default=10,
        ge=1,
        le=50
    )

    category: str | None = None

    min_rating: float | None = Field(
        default=None,
        ge=0,
        le=5
    )

    max_price: float | None = Field(
        default=None,
        ge=0
    )


# ============================================================
# COMMON FILTER RESPONSE
# ============================================================

def filter_response(
    category,
    min_rating,
    max_price
):

    return {
        "category": category,
        "min_rating": min_rating,
        "max_price": max_price
    }


# ============================================================
# TEXT SEARCH
# ============================================================

@router.post("/recommend")
def recommend_products(
    request: RecommendationRequest
):

    results = (
        recommendation_service.recommend(
            query=request.query,
            top_k=request.top_k,
            category=request.category,
            min_rating=request.min_rating,
            max_price=request.max_price
        )
    )

    return {

        "query":
            request.query,

        "search_type":
            "text",

        "count":
            len(results),

        "filters":
            filter_response(
                request.category,
                request.min_rating,
                request.max_price
            ),

        "results":
            results
    }


# ============================================================
# IMAGE SEARCH
# ============================================================

@router.post("/recommend/image")
async def recommend_by_image(
    image: UploadFile = File(...),

    top_k: int = Form(
        default=10,
        ge=1,
        le=50
    ),

    category: str | None = Form(
        default=None
    ),

    min_rating: float | None = Form(
        default=None,
        ge=0,
        le=5
    ),

    max_price: float | None = Form(
        default=None,
        ge=0
    )
):

    # --------------------------------------------------------
    # Validate image
    # --------------------------------------------------------

    if not image.content_type:

        raise HTTPException(
            status_code=400,
            detail="Image content type is missing."
        )

    allowed_types = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp"
    }

    if image.content_type not in allowed_types:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image format. "
                "Please upload JPG, PNG or WEBP."
            )
        )

    # --------------------------------------------------------
    # Read image bytes
    # --------------------------------------------------------

    try:

        image_bytes = await image.read()

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=f"Unable to read image: {error}"
        )

    if not image_bytes:

        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty."
        )

    # --------------------------------------------------------
    # Image size validation
    # --------------------------------------------------------

    max_size = 10 * 1024 * 1024

    if len(image_bytes) > max_size:

        raise HTTPException(
            status_code=400,
            detail="Image size must be less than 10 MB."
        )

    # --------------------------------------------------------
    # Call recommendation service
    # --------------------------------------------------------

    try:

        results = (
            recommendation_service
            .recommend_by_image(
                image_bytes=image_bytes,
                top_k=top_k,
                category=category,
                min_rating=min_rating,
                max_price=max_price
            )
        )

    except Exception as error:

        print(
            "IMAGE RECOMMENDATION ERROR:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to generate image "
                "recommendations."
            )
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {

        "query":
            None,

        "search_type":
            "image",

        "image_name":
            image.filename,

        "count":
            len(results),

        "filters":
            filter_response(
                category,
                min_rating,
                max_price
            ),

        "results":
            results
    }


# ============================================================
# TEXT + IMAGE MULTIMODAL SEARCH
# ============================================================

@router.post("/recommend/multimodal")
async def recommend_multimodal(
    image: UploadFile = File(...),

    query: str | None = Form(
        default=None
    ),

    top_k: int = Form(
        default=10,
        ge=1,
        le=50
    ),

    category: str | None = Form(
        default=None
    ),

    min_rating: float | None = Form(
        default=None,
        ge=0,
        le=5
    ),

    max_price: float | None = Form(
        default=None,
        ge=0
    ),

    text_weight: float = Form(
        default=0.5,
        ge=0,
        le=1
    ),

    image_weight: float = Form(
        default=0.5,
        ge=0,
        le=1
    )
):

    # --------------------------------------------------------
    # Validate query
    # --------------------------------------------------------

    cleaned_query = (
        query.strip()
        if query
        else ""
    )

    if not cleaned_query:

        raise HTTPException(
            status_code=400,
            detail=(
                "Text query is required "
                "for multimodal search."
            )
        )

    # --------------------------------------------------------
    # Validate image
    # --------------------------------------------------------

    if not image.content_type:

        raise HTTPException(
            status_code=400,
            detail="Image content type is missing."
        )

    allowed_types = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp"
    }

    if image.content_type not in allowed_types:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image format. "
                "Please upload JPG, PNG or WEBP."
            )
        )

    # --------------------------------------------------------
    # Validate weights
    # --------------------------------------------------------

    if (
        text_weight == 0
        and image_weight == 0
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Text and image weights "
                "cannot both be zero."
            )
        )

    # Normalize weights

    total_weight = (
        text_weight
        + image_weight
    )

    text_weight = (
        text_weight
        / total_weight
    )

    image_weight = (
        image_weight
        / total_weight
    )

    # --------------------------------------------------------
    # Read image
    # --------------------------------------------------------

    try:

        image_bytes = await image.read()

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=f"Unable to read image: {error}"
        )

    if not image_bytes:

        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty."
        )

    # --------------------------------------------------------
    # Image size
    # --------------------------------------------------------

    max_size = 10 * 1024 * 1024

    if len(image_bytes) > max_size:

        raise HTTPException(
            status_code=400,
            detail="Image size must be less than 10 MB."
        )

    # --------------------------------------------------------
    # Multimodal recommendation
    # --------------------------------------------------------

    try:

        results = (
            recommendation_service
            .recommend_multimodal(
                query=cleaned_query,
                image_bytes=image_bytes,
                top_k=top_k,
                category=category,
                min_rating=min_rating,
                max_price=max_price,
                text_weight=text_weight,
                image_weight=image_weight
            )
        )

    except Exception as error:

        print(
            "MULTIMODAL RECOMMENDATION ERROR:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to generate multimodal "
                "recommendations."
            )
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {

        "query":
            cleaned_query,

        "search_type":
            "text_image",

        "image_name":
            image.filename,

        "weights": {

            "text":
                round(
                    text_weight,
                    3
                ),

            "image":
                round(
                    image_weight,
                    3
                )
        },

        "count":
            len(results),

        "filters":
            filter_response(
                category,
                min_rating,
                max_price
            ),

        "results":
            results
    }