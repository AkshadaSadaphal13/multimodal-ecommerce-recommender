import ProductCard from "./ProductCard";

function getProductImageUrls(product) {
  const collect = (value) => {
    if (!value) return [];
    if (typeof value === "string") {
      const trimmed = value.trim();
      if (/^https?:\/\//i.test(trimmed)) return [trimmed];
      try { return collect(JSON.parse(trimmed)); } catch {
        try { return collect(JSON.parse(trimmed.replace(/'/g, '"'))); } catch { return []; }
      }
    }
    if (Array.isArray(value)) return value.flatMap(collect);
    if (typeof value === "object") return ["hi_res", "large", "medium", "thumb", "url"].flatMap((key) => collect(value[key]));
    return [];
  };
  return [...new Set([
    ...collect(product?.image_url),
    ...collect(product?.image_urls),
    ...collect(product?.images),
    ...collect(product?.hi_res),
    ...collect(product?.large),
    ...collect(product?.medium),
  ])].filter((url) => !/\._(?:SX\d+_SY\d+|SS\d+)_/i.test(url));
}

function ProductGrid({
  products = [],
  wishlist = [],
  bag = [],
  onWishlist,
  onAddToBag,
  onViewDetails,
  className = "",
}) {
  if (!products.length) {
    return null;
  }

  const usedImages = new Set();
  const seenDesignGroups = new Map();
  const productsWithImageChoices = products.map((product) => {
    const imageUrls = getProductImageUrls(product);
    const title = String(product.title || "");
    const designLabel = title.match(/\(([^)]*(?:design|surprise box)[^)]*)\)/i)?.[1]?.trim().toLowerCase();
    const designGroup = designLabel
      ? `${String(product.main_category || product.category || "").toLowerCase()}|${designLabel}`
      : "";
    const designOccurrence = designGroup ? (seenDesignGroups.get(designGroup) || 0) : 0;
    if (designGroup) seenDesignGroups.set(designGroup, designOccurrence + 1);

    let preferredImageIndex = -1;
    if (designOccurrence > 0) {
      preferredImageIndex = imageUrls.findIndex((url, index) => index > 0 && !usedImages.has(url));
    }
    if (preferredImageIndex < 0) {
      preferredImageIndex = imageUrls.findIndex((url) => !usedImages.has(url));
    }
    if (preferredImageIndex >= 0) usedImages.add(imageUrls[preferredImageIndex]);
    return { product, preferredImageIndex };
  });

  return (
    <div className={`product-grid ${className}`}>

      {productsWithImageChoices.map(
        ({ product, preferredImageIndex }, index) => (

          <ProductCard
            key={`${product.product_id || `${product.title}-${index}`}-${preferredImageIndex}`}

            product={{
              ...product,
              rank:
                product.rank ||
                index + 1,
            }}

            preferredImageIndex={preferredImageIndex}

            wishlist={
              wishlist
            }

            bag={
              bag
            }

            onWishlist={
              onWishlist
            }

            onAddToBag={
              onAddToBag
            }

            onViewDetails={
              onViewDetails
            }
          />

        )
      )}

    </div>
  );
}

export default ProductGrid;
