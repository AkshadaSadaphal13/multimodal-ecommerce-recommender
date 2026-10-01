import ProductCard from "./ProductCard";

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

  return (
    <div className={`product-grid ${className}`}>

      {products.map(
        (product, index) => (

          <ProductCard
            key={
              product.product_id ||
              `${product.title}-${index}`
            }

            product={{
              ...product,
              rank:
                product.rank ||
                index + 1,
            }}

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
