import { useEffect, useMemo, useState } from "react";

function getImageUrls(product) {
  const values = [];

  const add = (value) => {
    if (value == null) return;

    if (typeof value === "string") {
      const text = value.trim();
      if (!text) return;

      if (/^https?:\/\//i.test(text)) {
        values.push(text);
        return;
      }

      // Some CSV/API responses contain the original list as a JSON/Python string.
      for (const parser of [JSON.parse]) {
        try {
          const parsed = parser(text);
          add(parsed);
          return;
        } catch (_) {}
      }

      // Also support Python-style single-quoted list/dict strings.
      try {
        const parsed = JSON.parse(text.replace(/\'/g, '\"'));
        add(parsed);
        return;
      } catch (_) {}

      const matches = text.match(/https?:\/\/[^\s\"'\]\[{},]+/g) || [];
      values.push(...matches);
      return;
    }

    if (Array.isArray(value)) {
      value.forEach(add);
      return;
    }

    if (typeof value === "object") {
      // Amazon commonly uses hi_res / large / medium / thumb / url.
      ["hi_res", "large", "medium", "thumb", "url"].forEach((key) => add(value[key]));
      Object.entries(value).forEach(([key, item]) => {
        if (!["hi_res", "large", "medium", "thumb", "url"].includes(key)) add(item);
      });
    }
  };

  add(product?.image_urls);
  add(product?.images);
  add(product?.image_url);

  return [...new Set(values.filter((url) => /^https?:\/\//i.test(url)))];
}

function formatPrice(value) {
  if (value === null || value === undefined || value === "") return "Price unavailable";
  const number = Number(value);
  if (!Number.isFinite(number)) return "Price unavailable";
  return `₹${number.toLocaleString("en-IN")}`;
}

function sentimentClass(value) {
  const text = String(value || "mixed").toLowerCase();
  if (text.includes("positive")) return "positive";
  if (text.includes("negative")) return "negative";
  return "mixed";
}

function ProductImage({ product, className = "product-card-image" }) {
  const urls = useMemo(() => getImageUrls(product), [product]);
  const [index, setIndex] = useState(0);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setIndex(0);
    setFailed(false);
  }, [product?.product_id, urls.join("|")]);

  const current = urls[index];

  if (!current || failed) {
    return (
      <div className="product-image-fallback" role="img" aria-label="Product image unavailable">
        <span>✦</span>
        <small>Image unavailable</small>
      </div>
    );
  }

  return (
    <img
      className={className}
      src={current}
      alt={product?.title || "Product"}
      loading="lazy"
      decoding="async"
      referrerPolicy="no-referrer"
      onError={() => {
        if (index < urls.length - 1) {
          setIndex((value) => value + 1);
        } else {
          setFailed(true);
        }
      }}
    />
  );
}

export default function ProductGrid({
  products = [],
  wishlist = [],
  bag = [],
  onWishlist,
  onAddToBag,
  onViewDetails,
}) {
  const wishlistIds = useMemo(
    () => new Set(wishlist.map((item) => String(item.product_id))),
    [wishlist]
  );

  const uniqueProducts = useMemo(() => {
    const seen = new Set();
    return products.filter((product) => {
      const id = String(product?.product_id || "");
      if (!id || seen.has(id)) return false;
      seen.add(id);
      return true;
    });
  }, [products]);

  if (!uniqueProducts.length) {
    return (
      <div className="product-grid-empty">
        <div className="empty-icon">✦</div>
        <h3>No products found</h3>
        <p>Try a broader search or change your filters.</p>
      </div>
    );
  }

  return (
    <div className="premium-product-grid">
      {uniqueProducts.map((product, index) => {
        const id = String(product.product_id);
        const match = Math.max(0, Math.min(100, Number(product.similarity || 0) * 100));
        const positive = Math.max(0, Math.min(100, Number(product.positive_review_percentage || 0)));
        const negative = Math.max(0, Math.min(100, Number(product.negative_review_percentage || 0)));
        const isWishlisted = wishlistIds.has(id);
        const inBag = bag.some((item) => String(item.product_id) === id);

        return (
          <article className="premium-product-card" key={id}>
            <div className="premium-card-image-wrap">
              <div className="premium-rank">#{index + 1}</div>
              <button type="button" className={`premium-wishlist ${isWishlisted ? "active" : ""}`} aria-label={isWishlisted ? "Remove from wishlist" : "Add to wishlist"} onClick={() => onWishlist?.(product)}>
                {isWishlisted ? "♥" : "♡"}
              </button>
              <ProductImage product={product} />
              <div className="premium-image-overlay">
                <button type="button" onClick={() => onViewDetails?.(product)}>Quick View</button>
              </div>
            </div>

            <div className="premium-card-body">
              <div className="premium-card-topline">
                <span>{product.brand || product.store || "Marketplace"}</span>
                <span>{product.category || product.main_category || "Product"}</span>
              </div>
              <button type="button" className="premium-product-title" onClick={() => onViewDetails?.(product)}>
                {product.title || "Untitled product"}
              </button>
              <div className="premium-rating-row">
                <span className="stars">★</span>
                <strong>{Number(product.rating || 0).toFixed(1)}</strong>
                <span className="review-count">{Number(product.review_count || product.rating_number || 0).toLocaleString("en-IN")} reviews</span>
              </div>
              <div className="premium-price-row">
                <strong>{formatPrice(product.price)}</strong>
                <span className="match-pill">AI {match.toFixed(0)}%</span>
              </div>
              <div className="premium-match-block">
                <div className="premium-match-head"><span>AI MATCH</span><strong>{match.toFixed(1)}%</strong></div>
                <div className="premium-match-track"><span style={{ width: `${match}%` }} /></div>
              </div>
              <div className="premium-review-box">
                <div className="premium-review-head"><span>Customer feedback</span><span className={`sentiment-chip ${sentimentClass(product.overall_sentiment)}`}>{product.overall_sentiment || "Mixed"}</span></div>
                <div className="sentiment-line"><span>Positive</span><div><i style={{ width: `${positive}%` }} /></div><b>{positive.toFixed(0)}%</b></div>
                <div className="sentiment-line negative-line"><span>Negative</span><div><i style={{ width: `${negative}%` }} /></div><b>{negative.toFixed(0)}%</b></div>
              </div>
              <div className="premium-reason"><span className="reason-spark">✦</span><div><strong>Why recommended?</strong><p>{product.reason || "Strong semantic match with your search."}</p></div></div>
              <div className="premium-card-actions">
                <button type="button" className="premium-details-button" onClick={() => onViewDetails?.(product)}>View Details</button>
                <button type="button" className={`premium-bag-button ${inBag ? "added" : ""}`} aria-label="Add to bag" onClick={() => onAddToBag?.(product)}>{inBag ? "✓" : "＋"}</button>
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
