import ProductCard from "./ProductCard";

function ProductGrid({
  products = [],
  wishlist = [],
  bag = [],
  onWishlist,
  onAddToBag,
  onViewDetails,
}) {
  if (!products.length) {
    return null;
  }

  return (
    <div className="product-grid">

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