import { useState } from "react";

function ProductCard({
  product,
  preferredImageIndex = 0,
  wishlist = [],
  onWishlist,
  onAddToBag,
  onViewDetails,
}) {
  const [imageIndex, setImageIndex] = useState(preferredImageIndex);
  /* =====================================================
     IMAGE
  ===================================================== */

  const getImageUrls = (value) => {
    if (!value) return [];
    if (typeof value === "string") {
      const trimmed = value.trim();
      if (/^https?:\/\//i.test(trimmed)) return [trimmed];
      try { return getImageUrls(JSON.parse(trimmed)); } catch {
        try { return getImageUrls(trimmed.replace(/'/g, '"') && JSON.parse(trimmed.replace(/'/g, '"'))); } catch { return []; }
      }
    }
    if (Array.isArray(value)) return value.flatMap(getImageUrls);
    if (typeof value === "object") {
      return ["hi_res", "large", "medium", "thumb", "url"].flatMap((key) => getImageUrls(value[key]));
    }
    return [];
  };
  const imageUrls = [...new Set([
    ...getImageUrls(product?.image_url),
    ...getImageUrls(product?.image_urls),
    ...getImageUrls(product?.images),
    ...getImageUrls(product?.hi_res),
    ...getImageUrls(product?.large),
    ...getImageUrls(product?.medium),
  ])].filter((url) => !/\._(?:SX\d+_SY\d+|SS\d+)_/i.test(url));
  const imageUrl = imageUrls[imageIndex];


  /* =====================================================
     SAFE VALUES
  ===================================================== */

  const similarity = Number(
    product?.similarity || 0
  );

  const rating = Number(product?.rating ?? product?.average_rating ?? 0);
  const brand = product?.brand || product?.store || "";

  const price =
    product?.price !== null &&
    product?.price !== undefined &&
    product?.price !== ""
      ? Number(product.price)
      : null;
  const originalPrice = Number(product?.original_price ?? product?.list_price ?? product?.mrp ?? 0);
  const discountPercent = Number(product?.discount_percentage ?? (originalPrice > (price || 0) && price > 0 ? Math.round((1 - price / originalPrice) * 100) : 0));

  const reviewCount = Number(product?.review_count ?? product?.rating_number ?? 0);

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

  const handleImageError = () => setImageIndex((current) => current + 1);


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
            onError={handleImageError}
          />
        ) : (
          <div className="image-placeholder product-art-fallback">
            <span className="fallback-mark">{(brand || product?.title || "F").trim().slice(0, 1).toUpperCase()}</span>
            <small>{product?.category || product?.main_category || "A GOOD FIND"}</small>
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

        {brand && (
          <div className="product-brand">
            {brand}
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
          {discountPercent > 0 && (
            <div className="discount-detail">{originalPrice > 0 && <del>{`₹${originalPrice.toLocaleString("en-IN")}`}</del>}<span>{discountPercent}% OFF</span></div>
          )}

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
