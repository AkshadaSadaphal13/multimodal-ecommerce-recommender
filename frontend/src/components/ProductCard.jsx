function ProductCard({
  product,
  wishlist = [],
  onWishlist,
  onAddToBag,
  onViewDetails,
}) {
  /* =====================================================
     IMAGE
  ===================================================== */

  const getImageUrl = () => {
    if (product?.image_url) {
      return product.image_url;
    }

    if (typeof product?.images === "string") {
      return product.images;
    }

    if (Array.isArray(product?.images)) {
      const first = product.images[0];

      if (typeof first === "string") {
        return first;
      }

      if (first && typeof first === "object") {
        return (
          first.large ||
          first.medium ||
          first.thumb ||
          first.url ||
          null
        );
      }
    }

    return null;
  };

  const imageUrl = getImageUrl();


  /* =====================================================
     SAFE VALUES
  ===================================================== */

  const similarity = Number(
    product?.similarity || 0
  );

  const rating = Number(
    product?.rating || 0
  );

  const price =
    product?.price !== null &&
    product?.price !== undefined &&
    product?.price !== ""
      ? Number(product.price)
      : null;

  const reviewCount = Number(
    product?.review_count || 0
  );

  const positivePercentage = Number(
    product?.positive_review_percentage || 0
  );

  const negativePercentage = Number(
    product?.negative_review_percentage || 0
  );

  const sentiment =
    product?.overall_sentiment ||
    "Mixed";


  /* =====================================================
     WISHLIST STATE
  ===================================================== */

  const isWishlisted = wishlist.some(
    (item) =>
      item?.product_id ===
      product?.product_id
  );


  /* =====================================================
     SENTIMENT
  ===================================================== */

  const getSentimentClass = () => {
    const value =
      sentiment.toLowerCase();

    if (
      value.includes("positive")
    ) {
      return "positive";
    }

    if (
      value.includes("negative")
    ) {
      return "negative";
    }

    return "mixed";
  };


  const sentimentClass =
    getSentimentClass();


  /* =====================================================
     RECOMMENDATION REASON
  ===================================================== */

  const recommendationReason =
    product?.reason ||
    "Strong semantic match with your search."


  /* =====================================================
     PRICE
  ===================================================== */

  const formattedPrice =
    price !== null &&
    !Number.isNaN(price)
      ? `₹${price.toLocaleString(
          "en-IN",
          {
            maximumFractionDigits: 2,
          }
        )}`
      : "Price unavailable";


  /* =====================================================
     IMAGE ERROR
  ===================================================== */

  const handleImageError = (
    event
  ) => {
    event.currentTarget.style.display =
      "none";

    const parent =
      event.currentTarget.parentElement;

    if (parent) {
      parent.classList.add(
        "image-load-error"
      );
    }
  };


  /* =====================================================
     RENDER
  ===================================================== */

  return (
    <article className="product-card">


      {/* =================================================
          IMAGE
      ================================================= */}

      <div className="product-image-wrapper">


        {/* RANK */}

        <div className="product-rank">
          #{product?.rank || "—"}
        </div>


        {/* WISHLIST */}

        <button
          className={`card-wishlist ${
            isWishlisted
              ? "wishlisted"
              : ""
          }`}
          onClick={() => {
            if (onWishlist) {
              onWishlist(product);
            }
          }}
          title={
            isWishlisted
              ? "Remove from wishlist"
              : "Add to wishlist"
          }
        >
          {isWishlisted
            ? "♥"
            : "♡"}
        </button>


        {/* IMAGE */}

        {imageUrl ? (
          <img
            src={imageUrl}
            alt={
              product?.title ||
              "Recommended product"
            }
            className="product-image"
            loading="lazy"
            onError={
              handleImageError
            }
          />
        ) : (
          <div className="image-placeholder">
            <span>
              🛍
            </span>

            <small>
              Image unavailable
            </small>
          </div>
        )}


        {/* QUICK ADD */}

        <button
          className="quick-add-button"
          onClick={() => {
            if (onAddToBag) {
              onAddToBag(product);
            }
          }}
        >
          ADD TO BAG
        </button>

      </div>


      {/* =================================================
          PRODUCT INFORMATION
      ================================================= */}

      <div className="product-content">


        {/* BRAND */}

        {product?.brand && (
          <div className="product-brand">
            {product.brand}
          </div>
        )}


        {/* TITLE */}

        <h3 className="product-title">
          {product?.title ||
            "Untitled Product"}
        </h3>


        {/* CATEGORY */}

        {(
          product?.category ||
          product?.main_category
        ) && (
          <div className="product-category">
            {
              product.category ||
              product.main_category
            }
          </div>
        )}


        {/* =================================================
            RATING + REVIEWS
        ================================================= */}

        <div className="product-meta-row">

          <div className="product-rating">

            <span className="rating-star">
              ★
            </span>

            <span>
              {rating > 0
                ? rating.toFixed(1)
                : "N/A"}
            </span>

          </div>


          <span className="meta-divider">
            •
          </span>


          <span className="review-count">

            {reviewCount > 0
              ? `${reviewCount} reviews`
              : "No reviews"}

          </span>

        </div>


        {/* =================================================
            PRICE
        ================================================= */}

        <div className="product-price-row">

          <div className="product-price">
            {formattedPrice}
          </div>

        </div>


        {/* =================================================
            AI MATCH
        ================================================= */}

        <div className="similarity-section">

          <div className="similarity-header">

            <span>
              AI MATCH
            </span>

            <strong>
              {(
                similarity * 100
              ).toFixed(1)}
              %
            </strong>

          </div>


          <div className="similarity-bar">

            <div
              className="similarity-fill"
              style={{
                width: `${Math.min(
                  similarity * 100,
                  100
                )}%`,
              }}
            />

          </div>

        </div>


        {/* =================================================
            REVIEW SENTIMENT
        ================================================= */}

        <div className="review-summary">


          <div className="review-summary-header">

            <span>
              Customer Reviews
            </span>

            <strong
              className={`sentiment-badge ${sentimentClass}`}
            >
              {sentiment}
            </strong>

          </div>


          <div className="sentiment-row">

            <span>
              Positive
            </span>

            <div className="sentiment-track">

              <div
                className="sentiment-positive"
                style={{
                  width: `${Math.min(
                    positivePercentage,
                    100
                  )}%`,
                }}
              />

            </div>

            <small>
              {positivePercentage.toFixed(0)}%
            </small>

          </div>


          <div className="sentiment-row">

            <span>
              Negative
            </span>

            <div className="sentiment-track">

              <div
                className="sentiment-negative"
                style={{
                  width: `${Math.min(
                    negativePercentage,
                    100
                  )}%`,
                }}
              />

            </div>

            <small>
              {negativePercentage.toFixed(0)}%
            </small>

          </div>

        </div>


        {/* =================================================
            WHY RECOMMENDED
        ================================================= */}

        <div className="recommendation-reason">

          <span className="reason-icon">
            ✨
          </span>


          <div>

            <strong>
              Why recommended?
            </strong>

            <p>
              {recommendationReason}
            </p>

          </div>

        </div>


        {/* =================================================
            ACTIONS
        ================================================= */}

        <div className="card-actions">


          <button
            className="view-details-btn"
            onClick={() => {

              if (onViewDetails) {
                onViewDetails(
                  product
                );
              }

            }}
          >
            View Details
          </button>


          <button
            className="card-bag-btn"
            onClick={() => {

              if (onAddToBag) {
                onAddToBag(
                  product
                );
              }

            }}
          >
            🛍
          </button>

        </div>

      </div>

    </article>
  );
}

export default ProductCard;