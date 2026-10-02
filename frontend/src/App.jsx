import {
  useEffect,
  useMemo,
  useState,
} from "react";

import "./App.css";
import "./App.additions.css";
import "./App.theme.css";
import "./App.myntra.css";
import SearchBar from "./components/SearchBar";
import ProductGrid from "./components/ProductGrid";

import {
  getRecommendations,
  getImageRecommendations,
  getMultimodalRecommendations,
  getProducts,
} from "./services/api";
import { trackActivity } from "./services/userHistory";


/* =========================================================
   HELPERS
========================================================= */

function getImageUrl(product) {
  return getProductImageUrls(product)[0] || null;
}

function getProductImageUrls(product) {
  const collect = (value) => {
    if (!value) return [];
    if (typeof value === "string") {
      const text = value.trim();
      if (/^https?:\/\//i.test(text)) return [text];
      try { return collect(JSON.parse(text)); } catch { return []; }
    }
    if (Array.isArray(value)) return value.flatMap(collect);
    if (typeof value === "object") return ["hi_res", "large", "medium", "thumb", "url"].flatMap((key) => collect(value[key]));
    return [];
  };
  return [...new Set([collect(product?.image_url), collect(product?.image_urls), collect(product?.images)].flat())];
}


function getProductPrice(product) {
  if (
    product?.price === null ||
    product?.price === undefined ||
    product?.price === ""
  ) {
    return null;
  }

  const value = Number(product.price);

  if (
    Number.isNaN(value) ||
    !Number.isFinite(value)
  ) {
    return null;
  }

  return value;
}


function formatPrice(value) {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(Number(value))
  ) {
    return "Price unavailable";
  }

  return `₹${Number(value).toLocaleString("en-IN")}`;
}


function createOrderId() {
  return `RAI${Math.floor(
    100000 + Math.random() * 900000
  )}`;
}


function getCurrentDate() {
  return new Date().toLocaleDateString(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }
  );
}


/* =========================================================
   APP
========================================================= */

function App() {

  /* =======================================================
     SEARCH
  ======================================================= */

  const [query, setQuery] =
    useState("black running shoes");

  const [products, setProducts] =
    useState([]);

  const [catalog, setCatalog] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogLimit, setCatalogLimit] = useState(12);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [searched, setSearched] =
    useState(false);

  /* =======================================================
     IMAGE / MULTIMODAL SEARCH
  ======================================================= */

  const [selectedImage, setSelectedImage] =
    useState(null);

  const [searchMode, setSearchMode] =
    useState("text");

  const [imagePreview, setImagePreview] =
    useState("");


  /* =======================================================
     FILTERS
  ======================================================= */

  const [topK, setTopK] =
    useState(10);

  const [minimumRating, setMinimumRating] =
    useState(0);

  const [maximumPrice, setMaximumPrice] =
    useState("");

  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedBrand, setSelectedBrand] = useState("");

  const [sortBy, setSortBy] =
    useState("recommendation");

  const [showFilters, setShowFilters] =
    useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);


  /* =======================================================
     PANELS
  ======================================================= */

  const [activePanel, setActivePanel] =
    useState(null);

  const [selectedProduct, setSelectedProduct] =
    useState(null);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);

  const [recentlyViewed, setRecentlyViewed] = useState(() => {
    try { return JSON.parse(localStorage.getItem("recomai_recently_viewed") || "[]"); }
    catch { return []; }
  });


  /* =======================================================
     WISHLIST
  ======================================================= */

  const [wishlist, setWishlist] =
    useState(() => {
      try {
        const saved =
          localStorage.getItem(
            "recomai_wishlist"
          );

        return saved
          ? JSON.parse(saved)
          : [];
      } catch {
        return [];
      }
    });


  /* =======================================================
     BAG
  ======================================================= */

  const [bag, setBag] =
    useState(() => {
      try {
        const saved =
          localStorage.getItem(
            "recomai_bag"
          );

        return saved
          ? JSON.parse(saved)
          : [];
      } catch {
        return [];
      }
    });


  /* =======================================================
     USER ACCOUNT
  ======================================================= */

  const [user, setUser] =
    useState(() => {
      try {
        const saved =
          localStorage.getItem(
            "recomai_user"
          );

        return saved
          ? JSON.parse(saved)
          : null;
      } catch {
        return null;
      }
    });


  /* =======================================================
     ORDER HISTORY
  ======================================================= */

  const [orders, setOrders] =
    useState(() => {
      try {
        const saved =
          localStorage.getItem(
            "recomai_orders"
          );

        return saved
          ? JSON.parse(saved)
          : [];
      } catch {
        return [];
      }
    });


  /* =======================================================
     LOGIN / SIGNUP
  ======================================================= */

  const [authMode, setAuthMode] =
    useState("login");

  const [showAuth, setShowAuth] =
    useState(false);

  const [authData, setAuthData] =
    useState({
      name: "",
      email: "",
      password: "",
    });


  /* =======================================================
     CHECKOUT
  ======================================================= */

  const [showCheckout, setShowCheckout] =
    useState(false);

  const [orderPlaced, setOrderPlaced] =
    useState(false);

  const [lastOrder, setLastOrder] =
    useState(null);

  const [checkoutData, setCheckoutData] =
    useState({
      name: "",
      phone: "",
      address: "",
      city: "",
      pincode: "",
      payment: "Cash on Delivery",
    });


  /* =======================================================
     BAG TOTAL
  ======================================================= */

  const bagTotal = useMemo(() => {
    return bag.reduce(
      (total, item) => {
        const price =
          getProductPrice(item);

        if (price === null) {
          return total;
        }

        const quantity =
          Number(item.quantity || 1);

        return (
          total +
          price * quantity
        );
      },
      0
    );
  }, [bag]);

  useEffect(() => {
    let alive = true;
    getProducts(2500)
      .then((data) => { if (alive) setCatalog(Array.isArray(data.products) ? data.products : []); })
      .catch(() => { if (alive) setCatalog([]); })
      .finally(() => { if (alive) setCatalogLoading(false); });
    return () => { alive = false; };
  }, []);


  /* =======================================================
     SEARCH
  ======================================================= */

  const handleSearch = async (
    searchQuery = query,
    searchOptions = {}
  ) => {

    if (
      !searchQuery ||
      !searchQuery.trim()
    ) {
      return;
    }

    setQuery(searchQuery);
    void trackActivity({ type: "search", query: searchQuery, category: searchOptions.category ?? selectedCategory });

    setLoading(true);

    setError("");

    setSearched(true);

    try {

      let data;

      if (searchMode === "multimodal" && selectedImage) {
        data = await getMultimodalRecommendations(
          searchQuery,
          selectedImage,
          topK,
          {
            category: searchOptions.category ?? selectedCategory,
            minRating: minimumRating > 0 ? minimumRating : "",
            maxPrice: maximumPrice,
          },
          0.5,
          0.5
        );
      } else if (searchMode === "image" && selectedImage) {
        data = await getImageRecommendations(
          selectedImage,
          topK,
          {
            category: searchOptions.category ?? selectedCategory,
            minRating: minimumRating > 0 ? minimumRating : "",
            maxPrice: maximumPrice,
          }
        );
      } else {
        data = await getRecommendations(
          searchQuery,
          topK,
          {
            category: searchOptions.category ?? selectedCategory,
            minRating: minimumRating > 0 ? minimumRating : "",
            maxPrice: maximumPrice,
          }
        );
      }

      setProducts(
        data.results || []
      );

    } catch (err) {

      console.error(
        "Recommendation error:",
        err
      );

      setProducts([]);

      setError(
        "Unable to get recommendations. Make sure the FastAPI backend is running on port 8000."
      );

    } finally {

      setLoading(false);

    }
  };


  /* =======================================================
     IMAGE SELECTION
  ======================================================= */

  const handleImageSelect = (file) => {
    if (!file) {
      setSelectedImage(null);
      setImagePreview("");
      setSearchMode("text");
      return;
    }

    if (!file.type.startsWith("image/")) {
      alert("Please select a valid image file.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      alert("Please choose an image smaller than 10 MB.");
      return;
    }

    setSelectedImage(file);
    setImagePreview(URL.createObjectURL(file));
    setSearchMode(query.trim() ? "multimodal" : "image");
  };

  const clearSelectedImage = () => {
    setSelectedImage(null);
    setImagePreview("");
    setSearchMode("text");
  };


  /* =======================================================
     CATEGORY SEARCH
  ======================================================= */

  const handleCategorySearch = (
    category
  ) => {

    const realCategory = catalog.some((item) => item.main_category === category);
    setSelectedCategory(realCategory ? category : "");
    setSelectedBrand("");

    const categoryQueries = {

      "All Beauty":
        "beauty skincare products",

      "Digital Music":
        "digital music",

      "Video Games":
        "video games",

      "Health & Care":
        "health personal care products",

      "Gift Cards":
        "gift cards",

    };

    handleSearch(
      categoryQueries[category] ||
      category,
      { category: realCategory ? category : "" }
    );

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const handleDepartmentSearch = (department) => {
    const searches = {
      Men: "men clothing shoes",
      Women: "women fashion sandals",
      Kids: "kids games toys",
      Beauty: "beauty skincare products",
      Accessories: "accessories gift cards",
      Gadgets: "wireless headphones gaming controller",
      Sale: "gift cards popular products",
    };
    setSelectedCategory("");
    setSelectedBrand("");
    if (department === "Sale") setSortBy("price-low");
    handleSearch(searches[department] || department, { category: "" });
    document.getElementById("recommendations")?.scrollIntoView({ behavior: "smooth" });
  };


  /* =======================================================
     FILTERING
  ======================================================= */

  const filteredProducts =
    useMemo(() => {

      let result =
        [...products];


      if (
        minimumRating > 0
      ) {

        result =
          result.filter(
            (product) =>
              product.rating !== null &&
              product.rating !== undefined &&
              Number(product.rating ?? product.average_rating ?? 0) >=
                Number(minimumRating)
          );

      }

      if (selectedCategory) {
        result = result.filter((product) => (product.category || product.main_category) === selectedCategory);
      }

      if (selectedBrand) {
        result = result.filter((product) => (product.brand || product.store || "") === selectedBrand);
      }


      if (
        maximumPrice !== ""
      ) {

        result =
          result.filter(
            (product) => {

              const price =
                getProductPrice(
                  product
                );

              return (
                price !== null &&
                price <=
                  Number(maximumPrice)
              );

            }
          );

      }


      if (
        sortBy ===
        "recommendation"
      ) {

        result.sort(
          (a, b) =>
            Number(
              b.similarity || 0
            ) -
            Number(
              a.similarity || 0
            )
        );

      }


      if (
        sortBy === "rating"
      ) {

        result.sort(
          (a, b) =>
            Number(
              b.rating || 0
            ) -
            Number(
              a.rating || 0
            )
        );

      }


      if (
        sortBy ===
        "price-low"
      ) {

        result.sort(
          (a, b) => {

            const aPrice =
              getProductPrice(a);

            const bPrice =
              getProductPrice(b);

            return (
              (aPrice === null
                ? Infinity
                : aPrice) -
              (bPrice === null
                ? Infinity
                : bPrice)
            );

          }
        );

      }


      if (
        sortBy ===
        "price-high"
      ) {

        result.sort(
          (a, b) => {

            const aPrice =
              getProductPrice(a);

            const bPrice =
              getProductPrice(b);

            return (
              (bPrice === null
                ? -Infinity
                : bPrice) -
              (aPrice === null
                ? -Infinity
                : aPrice)
            );

          }
        );

      }


      const seenListings = new Set();
      return result.filter((product) => {
        const title = String(product.title || "").trim().toLowerCase();
        const store = String(product.brand || product.store || "").trim().toLowerCase();
        const category = String(product.category || product.main_category || "").trim().toLowerCase();
        const image = String(product.image_url || "").trim().toLowerCase();
        const listingKey = [title, store, category, image].join("|");
        if (!title || seenListings.has(listingKey)) return false;
        seenListings.add(listingKey);
        return true;
      });

    }, [
      products,
      minimumRating,
      maximumPrice,
      selectedCategory,
      selectedBrand,
      sortBy,
    ]);

  const availableCategories = useMemo(() => [...new Set(catalog.map((item) => item.main_category).filter(Boolean))].sort(), [catalog]);
  const availableBrands = useMemo(() => [...new Set(catalog.map((item) => item.store).filter(Boolean))].sort(), [catalog]);
  const catalogProducts = useMemo(() => {
    let result = [...catalog];
    if (selectedCategory) result = result.filter((item) => item.main_category === selectedCategory);
    if (selectedBrand) result = result.filter((item) => item.store === selectedBrand);
    if (minimumRating > 0) result = result.filter((item) => Number(item.average_rating || 0) >= minimumRating);
    if (maximumPrice !== "") result = result.filter((item) => getProductPrice(item) !== null && getProductPrice(item) <= Number(maximumPrice));
    if (sortBy === "rating") result.sort((a, b) => Number(b.average_rating || 0) - Number(a.average_rating || 0));
    if (sortBy === "price-low") result.sort((a, b) => (getProductPrice(a) ?? Infinity) - (getProductPrice(b) ?? Infinity));
    if (sortBy === "price-high") result.sort((a, b) => (getProductPrice(b) ?? -Infinity) - (getProductPrice(a) ?? -Infinity));
    return result;
  }, [catalog, selectedCategory, selectedBrand, minimumRating, maximumPrice, sortBy]);
  const relatedProducts = useMemo(() => {
    if (!selectedProduct) return [];
    const selectedCategoryName = selectedProduct.category || selectedProduct.main_category;
    const resultMatches = products.filter((item) => item.product_id !== selectedProduct.product_id && (item.category || item.main_category) === selectedCategoryName);
    const selectedFromResults = products.some((item) => item.product_id === selectedProduct.product_id);
    const source = selectedFromResults && resultMatches.length ? resultMatches : catalog.filter((item) => item.product_id !== selectedProduct.product_id && item.main_category === selectedCategoryName);
    return source.slice(0, 4);
  }, [selectedProduct, products, catalog]);
  const relatedAreAI = Boolean(selectedProduct && products.some((item) => item.product_id === selectedProduct.product_id) && relatedProducts.some((item) => products.some((result) => result.product_id === item.product_id)));


  /* =======================================================
     RESET FILTERS
  ======================================================= */

  const resetFilters = () => {

    setMinimumRating(0);

    setMaximumPrice("");
    setSelectedCategory("");
    setSelectedBrand("");

    setSortBy(
      "recommendation"
    );

    setTopK(10);
  };


  /* =======================================================
     WISHLIST
  ======================================================= */

  const handleWishlist = (
    product
  ) => {
    const isCurrentlyWishlisted = wishlist.some((item) => item.product_id === product.product_id);
    void trackActivity({ type: isCurrentlyWishlisted ? "wishlist_remove" : "wishlist", product });

    setWishlist(
      (current) => {

        const exists =
          current.some(
            (item) =>
              item.product_id ===
              product.product_id
          );

        let updated;

        if (exists) {

          updated =
            current.filter(
              (item) =>
                item.product_id !==
                product.product_id
            );

        } else {

          updated = [
            ...current,
            product,
          ];

        }

        localStorage.setItem(
          "recomai_wishlist",
          JSON.stringify(updated)
        );

        return updated;

      }
    );
  };


  /* =======================================================
     ADD TO BAG
  ======================================================= */

  const handleAddToBag = (
    product
  ) => {
    void trackActivity({ type: "cart", product });

    setBag(
      (current) => {

        const exists =
          current.find(
            (item) =>
              item.product_id ===
              product.product_id
          );

        let updated;

        if (exists) {

          updated =
            current.map(
              (item) =>
                item.product_id ===
                product.product_id
                  ? {
                      ...item,
                      quantity:
                        Number(
                          item.quantity ||
                            1
                        ) + 1,
                    }
                  : item
            );

        } else {

          updated = [
            ...current,
            {
              ...product,
              quantity: 1,
            },
          ];

        }

        localStorage.setItem(
          "recomai_bag",
          JSON.stringify(updated)
        );

        return updated;
      }
    );

    setActivePanel("bag");
  };


  /* =======================================================
     REMOVE BAG
  ======================================================= */

  const handleRemoveFromBag = (
    productId
  ) => {
    const removedProduct = bag.find((item) => item.product_id === productId);
    if (removedProduct) {
      void trackActivity({ type: "cart_remove", product: removedProduct });
    }

    setBag(
      (current) => {

        const updated =
          current.filter(
            (item) =>
              item.product_id !==
              productId
          );

        localStorage.setItem(
          "recomai_bag",
          JSON.stringify(updated)
        );

        return updated;
      }
    );
  };


  /* =======================================================
     QUANTITY
  ======================================================= */

  const changeBagQuantity = (
    productId,
    change
  ) => {
    const changedProduct = bag.find((item) => item.product_id === productId);
    if (changedProduct) {
      void trackActivity({ type: change > 0 ? "cart" : "cart_remove", product: changedProduct });
    }

    setBag(
      (current) => {

        const updated =
          current
            .map(
              (item) => {

                if (
                  item.product_id !==
                  productId
                ) {
                  return item;
                }

                const quantity =
                  Number(
                    item.quantity || 1
                  ) + change;

                return {
                  ...item,
                  quantity:
                    Math.max(
                      quantity,
                      1
                    ),
                };
              }
            );

        localStorage.setItem(
          "recomai_bag",
          JSON.stringify(updated)
        );

        return updated;
      }
    );
  };


  /* =======================================================
     AUTH INPUT
  ======================================================= */

  const handleAuthChange = (
    event
  ) => {

    const {
      name,
      value,
    } = event.target;

    setAuthData(
      (current) => ({
        ...current,
        [name]: value,
      })
    );
  };


  /* =======================================================
     LOGIN / SIGNUP
  ======================================================= */

  const handleAuthSubmit = (
    event
  ) => {

    event.preventDefault();


    if (
      authMode === "signup" &&
      !authData.name.trim()
    ) {

      alert(
        "Please enter your name."
      );

      return;
    }


    if (
      !authData.email.trim() ||
      !authData.password.trim()
    ) {

      alert(
        "Please enter email and password."
      );

      return;
    }


    const newUser = {

      name:
        authMode === "signup"
          ? authData.name
          : authData.email
              .split("@")[0],

      email:
        authData.email,

    };


    setUser(newUser);


    localStorage.setItem(
      "recomai_user",
      JSON.stringify(newUser)
    );


    setShowAuth(false);

    setAuthData({
      name: "",
      email: "",
      password: "",
    });

  };


  /* =======================================================
     LOGOUT
  ======================================================= */

  const handleLogout = () => {

    setUser(null);

    localStorage.removeItem(
      "recomai_user"
    );

    setActivePanel(null);
  };


  /* =======================================================
     PRODUCT DETAILS
  ======================================================= */

  const handleViewDetails = (
    product
  ) => {
    void trackActivity({ type: "view", product });
    const updated = [product, ...recentlyViewed.filter((item) => item.product_id !== product.product_id)].slice(0, 12);
    setRecentlyViewed(updated);
    localStorage.setItem("recomai_recently_viewed", JSON.stringify(updated));
    setSelectedImageIndex(0);
    setSelectedProduct(product);
  };


  /* =======================================================
     CHECKOUT
  ======================================================= */

  const handleCheckoutChange = (
    event
  ) => {

    const {
      name,
      value,
    } = event.target;

    setCheckoutData(
      (current) => ({
        ...current,
        [name]: value,
      })
    );
  };


  /* =======================================================
     OPEN CHECKOUT
  ======================================================= */

  const openCheckout = () => {

    if (bag.length === 0) {

      alert(
        "Your bag is empty."
      );

      return;
    }


    setCheckoutData(
      (current) => ({
        ...current,
        name:
          current.name ||
          user?.name ||
          "",
      })
    );


    setActivePanel(null);

    setShowCheckout(true);
  };


  /* =======================================================
     PLACE ORDER
  ======================================================= */

  const handlePlaceOrder = (
    event
  ) => {

    event.preventDefault();


    if (
      !checkoutData.name ||
      !checkoutData.phone ||
      !checkoutData.address ||
      !checkoutData.city ||
      !checkoutData.pincode
    ) {

      alert(
        "Please fill all delivery details."
      );

      return;
    }


    const newOrder = {

      orderId:
        createOrderId(),

      date:
        getCurrentDate(),

      status:
        "Confirmed",

      deliveryStatus:
        "Arriving in 3-5 days",

      payment:
        checkoutData.payment,

      total:
        bagTotal,

      customer:
        {
          name:
            checkoutData.name,

          phone:
            checkoutData.phone,

          address:
            checkoutData.address,

          city:
            checkoutData.city,

          pincode:
            checkoutData.pincode,
        },

      items:
        bag.map(
          (item) => ({
            ...item,
            quantity:
              Number(
                item.quantity || 1
              ),
          })
        ),

    };

    bag.forEach((item) => {
      void trackActivity({ type: "purchase", product: item });
    });


    const updatedOrders = [
      newOrder,
      ...orders,
    ];


    setOrders(
      updatedOrders
    );


    localStorage.setItem(
      "recomai_orders",
      JSON.stringify(
        updatedOrders
      )
    );


    setLastOrder(
      newOrder
    );


    setOrderPlaced(
      true
    );


    setBag([]);

    localStorage.setItem(
      "recomai_bag",
      JSON.stringify([])
    );

  };


  /* =======================================================
     CLOSE CHECKOUT
  ======================================================= */

  const closeCheckout = () => {

    setShowCheckout(false);

    setOrderPlaced(false);

    setLastOrder(null);
  };


  /* =======================================================
     OPEN ORDERS
  ======================================================= */

  const openOrders = () => {

    setActivePanel("orders");
  };


  /* =======================================================
     DELETE ORDER HISTORY
  ======================================================= */

  const clearOrders = () => {

    const confirmed =
      window.confirm(
        "Are you sure you want to clear your order history?"
      );

    if (!confirmed) {
      return;
    }

    setOrders([]);

    localStorage.removeItem(
      "recomai_orders"
    );
  };


  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="app">

      <div className="store-announcement">STYLE THAT FEELS LIKE YOU <span>•</span> Discovery powered by your taste</div>


      {/* =====================================================
          NAVBAR
      ===================================================== */}

      <nav className={`navbar${mobileMenuOpen ? " mobile-menu-open" : ""}`}>


        <button
          className="brand"
          onClick={() =>
            window.scrollTo({
              top: 0,
              behavior: "smooth",
            })
          }
        >

          <div className="brand-icon">
            ✦
          </div>

          <span>
            RecomAI
          </span>

        </button>


        <button className="mobile-menu-toggle" aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"} aria-expanded={mobileMenuOpen} onClick={() => setMobileMenuOpen((open) => !open)}>
          <span></span><span></span><span></span>
        </button>

        <div className="navbar-links">
          {["Men", "Women", "Kids", "Beauty", "Accessories", "Gadgets", "Sale"].map((department) => (
            <button key={department} className={department === "Sale" ? "nav-sale" : ""} onClick={() => { handleDepartmentSearch(department); setMobileMenuOpen(false); }}>{department}</button>
          ))}
        </div>


        <div className="navbar-search">

          <span>
            ⌕
          </span>

          <input
            value={query}
            onChange={(event) =>
              setQuery(
                event.target.value
              )
            }
            onKeyDown={(event) => {

              if (
                event.key ===
                "Enter"
              ) {
                handleSearch();
              }

            }}
            placeholder="Search for products, brands and more"
          />

        </div>


        <div className="navbar-actions">


          {/* PROFILE */}

          <button
            className="nav-action"
            onClick={() =>
              setActivePanel(
                "profile"
              )
            }
          >

            <span>
              ♙
            </span>

            <small>
              Profile
            </small>

          </button>


          {/* WISHLIST */}

          <button
            className="nav-action"
            onClick={() =>
              setActivePanel(
                "wishlist"
              )
            }
          >

            <span>
              ♡
            </span>

            <small>
              Wishlist
            </small>

            {wishlist.length >
              0 && (

              <span className="nav-count">
                {wishlist.length}
              </span>

            )}

          </button>


          {/* BAG */}

          <button
            className="nav-action"
            onClick={() =>
              setActivePanel(
                "bag"
              )
            }
          >

            <span>
              🛍
            </span>

            <small>
              Bag
            </small>

            {bag.length >
              0 && (

              <span className="nav-count">
                {bag.length}
              </span>

            )}

          </button>


          <button className="nav-action nav-quick-link" onClick={openOrders} title="Orders">
            <span>▤</span><small>Orders</small>
          </button>

          <button className="nav-action nav-quick-link" onClick={() => setActivePanel("recent")} title="Recently viewed">
            <span>◷</span><small>Recent</small>
          </button>


        </div>

      </nav>


      {/* =====================================================
          HERO
      ===================================================== */}

      <header className="hero">

        <div className="hero-content">

          <div className="hero-copy">

            <div className="eyebrow">

              <span className="live-dot"></span>

              PERSONALIZED DISCOVERY, MADE SIMPLE

            </div>


            <h1>

              Discover products

              <br />

              <span>
                Made for you.
              </span>

            </h1>


            <p className="hero-subtitle">

              Find your next favourite across fashion, beauty, tech and more. Search naturally, upload a photo, and let multimodal AI bring the right finds to you.

            </p>


            <div className="hero-buttons">

              <button
                className="primary-hero-btn"
                onClick={() =>
                  document
                    .getElementById(
                      "catalog-edit"
                    )
                    ?.scrollIntoView({
                      behavior:
                        "smooth",
                    })
                }
              >
                SHOP NOW
              </button>


              <button
                className="secondary-hero-btn"
                onClick={() =>
                  document
                    .getElementById(
                      "ai-search"
                    )
                    ?.scrollIntoView({
                      behavior:
                        "smooth",
                    })
                }
              >
                AI RECOMMENDATIONS
              </button>

            </div>


            <div className="hero-stats">

              <div>
                <strong>
                  {catalog.length ? catalog.length.toLocaleString("en-IN") : "2,499"}
                </strong>

                <span>
                  REAL PRODUCTS
                </span>
              </div>


              <div>
                <strong>
                  3
                </strong>

                <span>
                  AI SIGNALS
                </span>
              </div>


              <div>
                <strong>
                  FAISS
                </strong>

                <span>
                  PICK YOUR VIBE
                </span>
              </div>

            </div>

          </div>


          <div className="hero-visual">
            <img className="hero-editorial-image" src="https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=1200&q=85" alt="Friends exploring a fashion collection" fetchPriority="high" />
            <div className="hero-image-shade"></div>

            <div className="ai-orbit orbit-one"></div>

            <div className="ai-orbit orbit-two"></div>

            <div className="ai-orbit orbit-three"></div>


            <div className="ai-core">

              <span>
                ✦
              </span>

              <strong>
                MULTIMODAL
              </strong>

              <small>
                AI ENGINE
              </small>

            </div>


            <div className="ai-node node-image">

              🖼️ Image

            </div>


            <div className="ai-node node-text">

              📄 Text

            </div>


            <div className="ai-node node-review">

              ⭐ Reviews

            </div>

          </div>

        </div>

      </header>


      {/* =====================================================
          SEARCH
      ===================================================== */}

      <section
        id="ai-search"
        className="ai-search-section"
      >

        <div className="section-label">
          ✦ AI-POWERED SEARCH
        </div>

        <h2>
          What are you looking for?
        </h2>

        <p className="section-description">
          Describe a product naturally.
          Our multimodal AI will find
          relevant recommendations.
        </p>


        <div className="large-search-box">

          <SearchBar
            value={query}
            onChange={(value) => {
              setQuery(value);
              if (selectedImage) {
                setSearchMode(value.trim() ? "multimodal" : "image");
              }
            }}
            onSearch={() => handleSearch()}
            loading={loading}
            selectedImage={selectedImage}
            imagePreview={imagePreview}
            onImageSelect={handleImageSelect}
            onClearImage={clearSelectedImage}
            searchMode={searchMode}
          />


          <div className="popular-searches">

            <span>
              Popular searches
            </span>


            <button
              onClick={() =>
                handleSearch(
                  "black running shoes"
                )
              }
            >
              Black running shoes
            </button>


            <button
              onClick={() =>
                handleSearch(
                  "beauty products"
                )
              }
            >
              Beauty products
            </button>


            <button
              onClick={() =>
                handleSearch(
                  "video games"
                )
              }
            >
              Video games
            </button>


            <button
              onClick={() =>
                handleSearch(
                  "health personal care products"
                )
              }
            >
              Health & Personal Care
            </button>

          </div>

        </div>

      </section>


      {/* =====================================================
          CATEGORIES
      ===================================================== */}

      <section
        id="categories"
        className="categories-section"
      >

        <div className="section-top-row">

          <div>

            <div className="section-label">
              SHOP BY CATEGORY
            </div>

            <h2>
              Explore our collection
            </h2>

          </div>

          <span className="category-caption">
            AI-powered discovery
          </span>

        </div>


        <div className="category-grid">


          {(availableCategories.length ? availableCategories : ["All Beauty", "Digital Music", "Gift Cards", "Health & Personal Care", "Video Games"]).map(
            (category, index) => (

              <button
                key={category}
                className={`category-card category-${index % 5}`}
                onClick={() =>
                  handleCategorySearch(
                    category
                  )
                }
              >

                {(() => {
                  const categoryProduct = catalog.find((item) => item.main_category === category && getProductImageUrls(item).length);
                  const image = categoryProduct ? getProductImageUrls(categoryProduct)[0] : "";
                  return image ? <img className="category-image" src={image} alt="" loading="lazy" onError={(event) => { event.currentTarget.style.display = "none"; }} /> : null;
                })()}

                <div className="category-icon">
                  {String(index + 1).padStart(2, "0")}
                </div>

                <small>
                  CATEGORY{" "}
                  {String(
                    index + 1
                  ).padStart(2, "0")}
                </small>

                <strong>
                  {category}
                </strong>

                <p>
                  Discover products
                </p>

                <span className="category-arrow">
                  →
                </span>

              </button>

            )
          )}

        </div>

      </section>


      {/* =====================================================
          FULL CATALOG EDIT
      ===================================================== */}

      <section className="catalog-edit-section" id="catalog-edit">
        <div className="catalog-edit-heading">
          <div>
            <span className="section-label">THE RECOMAI EDIT</span>
            <h2>Good things, found.</h2>
            <p>{catalogLoading ? "Loading products from your catalog…" : `${catalog.length.toLocaleString("en-IN")} products from your collection`}</p>
          </div>
          <div className="catalog-filter-row">
            <select aria-label="Filter catalog by category" value={selectedCategory} onChange={(event) => setSelectedCategory(event.target.value)}>
              <option value="">All categories</option>
              {availableCategories.map((category) => <option key={category} value={category}>{category}</option>)}
            </select>
            <select aria-label="Filter catalog by brand" value={selectedBrand} onChange={(event) => setSelectedBrand(event.target.value)}>
              <option value="">All brands</option>
              {availableBrands.slice(0, 100).map((brand) => <option key={brand} value={brand}>{brand}</option>)}
            </select>
            <select aria-label="Sort products" value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
              <option value="recommendation">Featured</option><option value="rating">Top rated</option><option value="price-low">Price: low to high</option><option value="price-high">Price: high to low</option>
            </select>
          </div>
        </div>
        {catalogProducts.length ? (
          <>
            <ProductGrid products={catalogProducts.slice(0, catalogLimit)} wishlist={wishlist} bag={bag} onWishlist={handleWishlist} onAddToBag={handleAddToBag} onViewDetails={handleViewDetails} className="catalog-product-grid" />
            {catalogProducts.length > catalogLimit && <button className="load-more-products" onClick={() => setCatalogLimit((limit) => limit + 12)}>LOAD MORE FINDS</button>}
          </>
        ) : !catalogLoading && <div className="catalog-empty">Start the FastAPI backend to load products from your local catalog.</div>}
      </section>


      {/* =====================================================
          AI WORKS
      ===================================================== */}

      <section
        id="how-ai-works"
        className="how-ai-section"
      >

        <div className="section-label">
          HOW IT WORKS
        </div>

        <h2>
          One query. Three AI signals.
        </h2>

        <p className="section-description">
          RecomAI combines product
          images, product text and
          customer reviews.
        </p>


        <div className="ai-pipeline">

          <div className="pipeline-card">
            🖼️
            <strong>Image</strong>
            <small>ResNet50</small>
          </div>

          <div className="pipeline-line">
            →
          </div>

          <div className="pipeline-card">
            📄
            <strong>Product Text</strong>
            <small>Sentence-BERT</small>
          </div>

          <div className="pipeline-line">
            →
          </div>

          <div className="pipeline-card">
            ⭐
            <strong>Reviews</strong>
            <small>Sentiment AI</small>
          </div>

          <div className="pipeline-line">
            →
          </div>

          <div className="pipeline-card highlight">
            ✦
            <strong>Multimodal Fusion</strong>
            <small>3 signals combined</small>
          </div>

          <div className="pipeline-line">
            →
          </div>

          <div className="pipeline-card">
            ⚡
            <strong>FAISS</strong>
            <small>Top-K Retrieval</small>
          </div>

        </div>

      </section>


      {/* =====================================================
          MAIN RESULTS
      ===================================================== */}

      <main className="main-content">


        {loading && (

          <section className="loading-section">

            <div className="loader"></div>

            <h3>
              Finding the best products...
            </h3>

            <p>
              AI is analyzing your search.
            </p>

          </section>

        )}


        {error && (

          <div className="error-box">

            <span>
              !
            </span>

            <div>

              <strong>
                Recommendation error
              </strong>

              <p>
                {error}
              </p>

            </div>

          </div>

        )}


        {!loading &&
          searched &&
          !error && (

            <section
              className="results-section"
              id="recommendations"
            >

              <div className="results-header">

                <div>

                  <div className="section-label">
                    AI RECOMMENDATIONS
                  </div>

                  <h2>
                    Recommended for you
                  </h2>

                  <p>
                    Results for{" "}
                    <strong>
                      "{query}"
                    </strong>
                  </p>

                </div>


                <div className="result-count">

                  <strong>
                    {
                      filteredProducts.length
                    }
                  </strong>

                  <span>
                    products found
                  </span>

                </div>

              </div>


              <div className="toolbar">

                <button
                  className="filter-toggle"
                  onClick={() =>
                    setShowFilters(
                      !showFilters
                    )
                  }
                >
                  ☷ Filters
                </button>


                <div className="toolbar-right">

                  <label>

                    Results

                    <select
                      value={topK}
                      onChange={(event) =>
                        setTopK(
                          Number(
                            event.target.value
                          )
                        )
                      }
                    >

                      <option value={5}>
                        Top 5
                      </option>

                      <option value={10}>
                        Top 10
                      </option>

                      <option value={20}>
                        Top 20
                      </option>

                    </select>

                  </label>


                  <label>

                    Sort

                    <select
                      value={sortBy}
                      onChange={(event) =>
                        setSortBy(
                          event.target.value
                        )
                      }
                    >

                      <option value="recommendation">
                        AI Recommendation
                      </option>

                      <option value="rating">
                        Highest Rating
                      </option>

                      <option value="price-low">
                        Price: Low to High
                      </option>

                      <option value="price-high">
                        Price: High to Low
                      </option>

                    </select>

                  </label>

                </div>

              </div>


              {showFilters && (

                <div className="filter-panel">

                  <div className="filter-item">

                    <label>Category</label>
                    <select value={selectedCategory} onChange={(event) => setSelectedCategory(event.target.value)}>
                      <option value="">All categories</option>
                      {availableCategories.map((category) => <option key={category} value={category}>{category}</option>)}
                    </select>

                  </div>

                  <div className="filter-item">

                    <label>Brand</label>
                    <select value={selectedBrand} onChange={(event) => setSelectedBrand(event.target.value)}>
                      <option value="">All brands</option>
                      {[...new Set(products.map((product) => product.brand || product.store).filter(Boolean))].sort().map((brand) => <option key={brand} value={brand}>{brand}</option>)}
                    </select>

                  </div>

                  <div className="filter-item">

                    <label>
                      Minimum Rating
                    </label>

                    <select
                      value={
                        minimumRating
                      }
                      onChange={(event) =>
                        setMinimumRating(
                          Number(
                            event.target.value
                          )
                        )
                      }
                    >

                      <option value={0}>
                        All ratings
                      </option>

                      <option value={3}>
                        3+ ⭐
                      </option>

                      <option value={4}>
                        4+ ⭐
                      </option>

                      <option value={4.5}>
                        4.5+ ⭐
                      </option>

                    </select>

                  </div>


                  <div className="filter-item">

                    <label>
                      Maximum Price
                    </label>

                    <input
                      type="number"
                      placeholder="Any price"
                      value={
                        maximumPrice
                      }
                      onChange={(event) =>
                        setMaximumPrice(
                          event.target.value
                        )
                      }
                    />

                  </div>


                  <button
                    className="reset-button"
                    onClick={
                      resetFilters
                    }
                  >
                    Reset Filters
                  </button>

                </div>

              )}


              {filteredProducts.length >
                0 ? (

                <ProductGrid
                  products={
                    filteredProducts
                  }

                  wishlist={
                    wishlist
                  }

                  bag={
                    bag
                  }

                  onWishlist={
                    handleWishlist
                  }

                  onAddToBag={
                    handleAddToBag
                  }

                  onViewDetails={
                    handleViewDetails
                  }
                />

              ) : (

                <div className="empty-results">

                  <h3>
                    No matching products
                  </h3>

                  <p>
                    Try another search
                    or reset your filters.
                  </p>

                  <button
                    onClick={
                      resetFilters
                    }
                  >
                    Reset Filters
                  </button>

                </div>

              )}

            </section>

          )}


        {!searched &&
          !loading &&
          !error && (

            <section className="welcome-section">

              <div className="welcome-icon">
                ✦
              </div>

              <div className="section-label">
                START EXPLORING
              </div>

              <h2>
                Your AI shopping assistant
              </h2>

              <p>
                Search naturally and
                discover products using
                image, text and customer
                review intelligence.
              </p>

            </section>

          )}

      </main>


      {/* =====================================================
          SIDE PANEL
      ===================================================== */}

      {activePanel && (

        <div
          className="side-panel-overlay"
          onClick={() =>
            setActivePanel(null)
          }
        >

          <aside
            className="side-panel"
            onClick={(event) =>
              event.stopPropagation()
            }
          >


            {/* =================================================
                PROFILE
            ================================================= */}

            {activePanel === "recent" && (
              <>
                <div className="panel-header"><div><span className="panel-kicker">YOUR BROWSING HISTORY</span><h2>Recently viewed</h2></div><button onClick={() => setActivePanel(null)}>×</button></div>
                {recentlyViewed.length ? <ProductGrid products={recentlyViewed} wishlist={wishlist} bag={bag} onWishlist={handleWishlist} onAddToBag={handleAddToBag} onViewDetails={handleViewDetails} className="recently-viewed-grid" /> : <div className="panel-empty"><div className="empty-icon">◷</div><h3>Nothing here just yet</h3><p>Open a product to find it again here.</p></div>}
              </>
            )}

            {activePanel ===
              "profile" && (

              <>

                <div className="panel-header">

                  <div>

                    <span className="panel-kicker">
                      MY ACCOUNT
                    </span>

                    <h2>
                      Profile
                    </h2>

                  </div>

                  <button
                    onClick={() =>
                      setActivePanel(null)
                    }
                  >
                    ×
                  </button>

                </div>


                {user ? (

                  <>

                    <div className="logged-user">

                      <div className="profile-avatar">
                        {user.name
                          ?.charAt(0)
                          ?.toUpperCase()}
                      </div>

                      <h3>
                        Hello, {user.name}
                      </h3>

                      <p>
                        {user.email}
                      </p>

                    </div>


                    <div className="account-stats">

                      <div>

                        <strong>
                          {orders.length}
                        </strong>

                        <span>
                          Orders
                        </span>

                      </div>


                      <div>

                        <strong>
                          {wishlist.length}
                        </strong>

                        <span>
                          Wishlist
                        </span>

                      </div>


                      <div>

                        <strong>
                          {bag.length}
                        </strong>

                        <span>
                          Bag
                        </span>

                      </div>

                    </div>


                    <div className="profile-links">

                      <button
                        onClick={
                          openOrders
                        }
                      >
                        <span>
                          📦
                        </span>

                        Orders

                        <b>
                          {orders.length}
                        </b>

                      </button>


                      <button
                        onClick={() =>
                          setActivePanel(
                            "wishlist"
                          )
                        }
                      >
                        <span>
                          ♡
                        </span>

                        Wishlist

                        <b>
                          {wishlist.length}
                        </b>

                      </button>


                      <button
                        onClick={() =>
                          setActivePanel(
                            "bag"
                          )
                        }
                      >
                        <span>
                          🛍
                        </span>

                        Shopping Bag

                        <b>
                          {bag.length}
                        </b>

                      </button>


                      <button>
                        <span>
                          📍
                        </span>

                        Saved Addresses

                      </button>


                      <button>
                        <span>
                          💬
                        </span>

                        Help & Support

                      </button>

                    </div>


                    <button
                      className="logout-button"
                      onClick={
                        handleLogout
                      }
                    >
                      LOGOUT
                    </button>

                  </>

                ) : (

                  <div className="profile-hero">

                    <div className="profile-avatar">
                      ♙
                    </div>

                    <h3>
                      Welcome to RecomAI
                    </h3>

                    <p>
                      Login to manage your
                      orders, wishlist and
                      personalized
                      recommendations.
                    </p>


                    <button
                      className="panel-primary-btn"
                      onClick={() => {

                        setAuthMode(
                          "login"
                        );

                        setShowAuth(
                          true
                        );

                      }}
                    >
                      LOGIN / SIGN UP
                    </button>


                    <div className="profile-links">

                      <button
                        onClick={() =>
                          setActivePanel(
                            "orders"
                          )
                        }
                      >
                        <span>
                          📦
                        </span>
                        Orders
                      </button>

                      <button
                        onClick={() =>
                          setActivePanel(
                            "wishlist"
                          )
                        }
                      >
                        <span>
                          ♡
                        </span>
                        Wishlist
                      </button>

                      <button
                        onClick={() =>
                          setActivePanel(
                            "bag"
                          )
                        }
                      >
                        <span>
                          🛍
                        </span>
                        Shopping Bag
                      </button>

                    </div>

                  </div>

                )}

              </>

            )}


            {/* =================================================
                ORDERS
            ================================================= */}

            {activePanel ===
              "orders" && (

              <>

                <div className="panel-header">

                  <div>

                    <span className="panel-kicker">
                      PURCHASE HISTORY
                    </span>

                    <h2>
                      My Orders
                    </h2>

                  </div>

                  <button
                    onClick={() =>
                      setActivePanel(
                        "profile"
                      )
                    }
                  >
                    ×
                  </button>

                </div>


                {orders.length ===
                  0 ? (

                  <div className="panel-empty">

                    <div className="empty-icon">
                      📦
                    </div>

                    <h3>
                      No orders yet
                    </h3>

                    <p>
                      Your completed orders
                      will appear here.
                    </p>

                    <button
                      className="panel-primary-btn"
                      onClick={() =>
                        setActivePanel(
                          null
                        )
                      }
                    >
                      START SHOPPING
                    </button>

                  </div>

                ) : (

                  <div className="orders-list">

                    <div className="orders-summary">

                      <strong>
                        {orders.length}
                      </strong>

                      <span>
                        total orders
                      </span>

                    </div>


                    {orders.map(
                      (order) => (

                        <div
                          className="order-card"
                          key={
                            order.orderId
                          }
                        >


                          <div className="order-card-header">

                            <div>

                              <span>
                                ORDER
                              </span>

                              <strong>
                                #{order.orderId}
                              </strong>

                            </div>


                            <span className="order-status">
                              ✓{" "}
                              {order.status}
                            </span>

                          </div>


                          <div className="order-date">

                            <span>
                              Ordered on
                            </span>

                            <strong>
                              {order.date}
                            </strong>

                          </div>


                          <div className="order-items">

                            {order.items
                              .slice(
                                0,
                                3
                              )
                              .map(
                                (
                                  item
                                ) => {

                                  const image =
                                    getImageUrl(
                                      item
                                    );

                                  return (

                                    <div
                                      className="order-item"
                                      key={
                                        item.product_id
                                      }
                                    >

                                      <div className="order-item-image">

                                        {image ? (

                                          <img
                                            src={
                                              image
                                            }
                                            alt={
                                              item.title
                                            }
                                          />

                                        ) : (

                                          <span>
                                            🛍
                                          </span>

                                        )}

                                      </div>


                                      <div>

                                        <strong>

                                          {item.title?.length >
                                          55

                                            ? `${item.title.slice(
                                                0,
                                                55
                                              )}...`

                                            : item.title}

                                        </strong>

                                        <small>

                                          Qty:{" "}
                                          {
                                            item.quantity
                                          }

                                        </small>

                                      </div>

                                    </div>

                                  );

                                }
                              )}

                          </div>


                          {order.items.length >
                            3 && (

                            <small className="more-items">
                              +
                              {order.items.length -
                                3}{" "}
                              more item(s)
                            </small>

                          )}


                          <div className="order-card-footer">

                            <div>

                              <span>
                                Total
                              </span>

                              <strong>
                                {formatPrice(
                                  order.total
                                )}
                              </strong>

                            </div>


                            <div>

                              <span>
                                Payment
                              </span>

                              <strong>
                                {
                                  order.payment
                                }
                              </strong>

                            </div>

                          </div>


                          <div className="delivery-status">

                            🚚{" "}

                            {
                              order.deliveryStatus
                            }

                          </div>

                        </div>

                      )
                    )}


                    <button
                      className="clear-orders"
                      onClick={
                        clearOrders
                      }
                    >
                      Clear Order History
                    </button>

                  </div>

                )}

              </>

            )}


            {/* =================================================
                WISHLIST
            ================================================= */}

            {activePanel ===
              "wishlist" && (

              <>

                <div className="panel-header">

                  <div>

                    <span className="panel-kicker">
                      SAVED PRODUCTS
                    </span>

                    <h2>
                      Wishlist
                    </h2>

                  </div>

                  <button
                    onClick={() =>
                      setActivePanel(null)
                    }
                  >
                    ×
                  </button>

                </div>


                {wishlist.length ===
                  0 ? (

                  <div className="panel-empty">

                    <div className="empty-icon">
                      ♡
                    </div>

                    <h3>
                      Your wishlist is empty
                    </h3>

                    <p>
                      Save products you love
                      and find them here later.
                    </p>

                  </div>

                ) : (

                  <div className="panel-products">

                    {wishlist.map(
                      (product) => {

                        const image =
                          getImageUrl(
                            product
                          );

                        return (

                          <div
                            className="panel-product"
                            key={
                              product.product_id
                            }
                          >

                            <div className="panel-product-image">

                              {image ? (

                                <img
                                  src={image}
                                  alt={
                                    product.title
                                  }
                                />

                              ) : (
                                <span>
                                  🛍
                                </span>
                              )}

                            </div>


                            <div className="panel-product-info">

                              <h4>
                                {
                                  product.title
                                }
                              </h4>

                              <span>
                                ★{" "}
                                {Number(
                                  product.rating ||
                                    0
                                ).toFixed(1)}
                              </span>

                              <strong>
                                {formatPrice(
                                  product.price
                                )}
                              </strong>


                              <div className="panel-product-actions">

                                <button
                                  onClick={() =>
                                    handleAddToBag(
                                      product
                                    )
                                  }
                                >
                                  Add to Bag
                                </button>

                                <button
                                  className="remove-btn"
                                  onClick={() =>
                                    handleWishlist(
                                      product
                                    )
                                  }
                                >
                                  Remove
                                </button>

                              </div>

                            </div>

                          </div>

                        );
                      }
                    )}

                  </div>

                )}

              </>

            )}


            {/* =================================================
                BAG
            ================================================= */}

            {activePanel ===
              "bag" && (

              <>

                <div className="panel-header">

                  <div>

                    <span className="panel-kicker">
                      SHOPPING BAG
                    </span>

                    <h2>
                      Your Bag
                    </h2>

                  </div>

                  <button
                    onClick={() =>
                      setActivePanel(null)
                    }
                  >
                    ×
                  </button>

                </div>


                {bag.length ===
                  0 ? (

                  <div className="panel-empty">

                    <div className="empty-icon">
                      🛍
                    </div>

                    <h3>
                      Your bag is empty
                    </h3>

                    <p>
                      Add products to your
                      bag and they will
                      appear here.
                    </p>

                  </div>

                ) : (

                  <>

                    <div className="panel-products">

                      {bag.map(
                        (item) => {

                          const image =
                            getImageUrl(
                              item
                            );

                          return (

                            <div
                              className="panel-product"
                              key={
                                item.product_id
                              }
                            >

                              <div className="panel-product-image">

                                {image ? (

                                  <img
                                    src={
                                      image
                                    }
                                    alt={
                                      item.title
                                    }
                                  />

                                ) : (

                                  <span>
                                    🛍
                                  </span>

                                )}

                              </div>


                              <div className="panel-product-info">

                                <h4>
                                  {
                                    item.title
                                  }
                                </h4>

                                <strong>
                                  {formatPrice(
                                    item.price
                                  )}
                                </strong>


                                <div className="quantity-controls">

                                  <button
                                    onClick={() =>
                                      changeBagQuantity(
                                        item.product_id,
                                        -1
                                      )
                                    }
                                  >
                                    −
                                  </button>

                                  <span>
                                    {
                                      item.quantity ||
                                      1
                                    }
                                  </span>

                                  <button
                                    onClick={() =>
                                      changeBagQuantity(
                                        item.product_id,
                                        1
                                      )
                                    }
                                  >
                                    +
                                  </button>

                                </div>


                                <button
                                  className="remove-btn"
                                  onClick={() =>
                                    handleRemoveFromBag(
                                      item.product_id
                                    )
                                  }
                                >
                                  Remove
                                </button>

                              </div>

                            </div>

                          );

                        }
                      )}

                    </div>


                    <div className="bag-summary">

                      <div>

                        <span>
                          Subtotal
                        </span>

                        <strong>
                          {formatPrice(
                            bagTotal
                          )}
                        </strong>

                      </div>


                      <p>
                        Delivery is free.
                      </p>


                      <button
                        className="checkout-btn"
                        onClick={
                          openCheckout
                        }
                      >
                        PLACE ORDER
                      </button>

                    </div>

                  </>

                )}

              </>

            )}

          </aside>

        </div>

      )}


      {/* =====================================================
          AUTH MODAL
      ===================================================== */}

      {showAuth && (

        <div
          className="auth-overlay"
          onClick={() =>
            setShowAuth(false)
          }
        >

          <div
            className="auth-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <button
              className="auth-close"
              onClick={() =>
                setShowAuth(false)
              }
            >
              ×
            </button>


            <div className="auth-logo">
              ✦
            </div>


            <h2>
              {authMode ===
              "login"
                ? "Welcome back"
                : "Create your account"}
            </h2>


            <p>
              {authMode ===
              "login"
                ? "Login to continue shopping with RecomAI."
                : "Create an account to manage orders and wishlist."}
            </p>


            <div className="auth-tabs">

              <button
                className={
                  authMode ===
                  "login"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setAuthMode(
                    "login"
                  )
                }
              >
                LOGIN
              </button>


              <button
                className={
                  authMode ===
                  "signup"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setAuthMode(
                    "signup"
                  )
                }
              >
                SIGN UP
              </button>

            </div>


            <form
              onSubmit={
                handleAuthSubmit
              }
            >


              {authMode ===
                "signup" && (

                <div className="auth-field">

                  <label>
                    Full Name
                  </label>

                  <input
                    type="text"
                    name="name"
                    value={
                      authData.name
                    }
                    onChange={
                      handleAuthChange
                    }
                    placeholder="Enter your name"
                  />

                </div>

              )}


              <div className="auth-field">

                <label>
                  Email
                </label>

                <input
                  type="email"
                  name="email"
                  value={
                    authData.email
                  }
                  onChange={
                    handleAuthChange
                  }
                  placeholder="you@example.com"
                />

              </div>


              <div className="auth-field">

                <label>
                  Password
                </label>

                <input
                  type="password"
                  name="password"
                  value={
                    authData.password
                  }
                  onChange={
                    handleAuthChange
                  }
                  placeholder="Enter password"
                />

              </div>


              <button
                className="auth-submit"
                type="submit"
              >

                {authMode ===
                "login"
                  ? "LOGIN"
                  : "CREATE ACCOUNT"}

              </button>

            </form>


            <small className="demo-note">
              Demo authentication: account
              information is stored locally
              in your browser.
            </small>

          </div>

        </div>

      )}


      {/* =====================================================
          PRODUCT DETAILS
      ===================================================== */}

      {selectedProduct && (

        <div
          className="product-modal-overlay"
          onClick={() =>
            setSelectedProduct(null)
          }
        >

          <div
            className="product-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <button
              className="product-modal-close"
              onClick={() =>
                setSelectedProduct(null)
              }
            >
              ×
            </button>


            <div className="product-modal-image">

              {getProductImageUrls(selectedProduct)[selectedImageIndex] ? (

                <img
                  src={getProductImageUrls(selectedProduct)[selectedImageIndex]}
                  alt={
                    selectedProduct.title
                  }
                  onError={() => setSelectedImageIndex((current) => current + 1)}
                />

              ) : (
                <span>
                  🛍
                </span>
              )}

              {getProductImageUrls(selectedProduct).length > 1 && (
                <div className="product-gallery-controls">
                  <button type="button" disabled={selectedImageIndex <= 0} onClick={() => setSelectedImageIndex((current) => current - 1)}>Previous</button>
                  <span>{Math.min(selectedImageIndex + 1, getProductImageUrls(selectedProduct).length)} / {getProductImageUrls(selectedProduct).length}</span>
                  <button type="button" disabled={selectedImageIndex >= getProductImageUrls(selectedProduct).length - 1} onClick={() => setSelectedImageIndex((current) => current + 1)}>Next</button>
                </div>
              )}

            </div>


            <div className="product-modal-content">

              <span className="modal-kicker">
                AI RECOMMENDED PRODUCT
              </span>


              <h2>
                {
                  selectedProduct.title
                }
              </h2>


              {selectedProduct.brand && (

                <p className="modal-brand">
                  {
                    selectedProduct.brand
                  }
                </p>

              )}


              <div className="modal-rating">

                ★{" "}
                {Number(
                  selectedProduct.rating ||
                    0
                ).toFixed(1)}

                <span>
                  {" "}
                  •{" "}
                  {Number(
                    selectedProduct.review_count ||
                      0
                  )}{" "}
                  reviews
                </span>

              </div>


              <div className="modal-price">

                {formatPrice(
                  selectedProduct.price
                )}

              </div>


              <div className="modal-match">

                <div>

                  <span>
                    AI MATCH SCORE
                  </span>

                  <strong>
                    {(
                      Number(
                        selectedProduct.similarity ||
                          0
                      ) * 100
                    ).toFixed(1)}
                    %
                  </strong>

                </div>


                <div className="modal-match-bar">

                  <span
                    style={{
                      width: `${Math.min(
                        Number(
                          selectedProduct.similarity ||
                            0
                        ) * 100,
                        100
                      )}%`,
                    }}
                  />

                </div>

              </div>


              <div className="modal-info-grid">

                <div>
                  <span>
                    CATEGORY
                  </span>

                  <strong>
                    {
                      selectedProduct.category ||
                      selectedProduct.main_category ||
                      "—"
                    }
                  </strong>
                </div>


                <div>
                  <span>
                    REVIEWS
                  </span>

                  <strong>
                    {Number(
                      selectedProduct.review_count ||
                        0
                    )}
                  </strong>
                </div>


                <div>
                  <span>
                    POSITIVE REVIEWS
                  </span>

                  <strong>
                    {Number(
                      selectedProduct.positive_review_percentage ||
                        0
                    ).toFixed(0)}
                    %
                  </strong>
                </div>


                <div>
                  <span>
                    SENTIMENT
                  </span>

                  <strong>
                    {
                      selectedProduct.overall_sentiment ||
                      "Mixed"
                    }
                  </strong>
                </div>

              </div>


              <div className="modal-reason">

                <strong>
                  ✨ Why this product?
                </strong>

                <p>
                  {
                    selectedProduct.reason ||
                    "This product has a strong semantic match with your search."
                  }
                </p>

              </div>


              {relatedProducts.length > 0 && (
                <div className="modal-related">
                  <strong>{relatedAreAI ? "AI PICKS FOR YOU" : "MORE FROM THIS CATEGORY"}</strong>
                  <div className="modal-related-products">
                    {relatedProducts.map((item) => (
                      <button key={item.product_id} onClick={() => handleViewDetails(item)}>
                        <div className="modal-related-image">
                          {getImageUrl(item) ? <img src={getImageUrl(item)} alt="" onError={(event) => { event.currentTarget.style.display = "none"; event.currentTarget.parentElement.querySelector(".related-image-fallback").style.display = "grid"; }} /> : null}
                          <span className="related-image-fallback" style={{ display: getImageUrl(item) ? "none" : "grid" }}>{(item.brand || item.store || item.title || "F").slice(0, 1)}</span>
                        </div>
                        <span>{item.title}</span>
                        <b>{formatPrice(item.price)}</b>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="modal-actions">

                <button
                  className="modal-wishlist-btn"
                  onClick={() =>
                    handleWishlist(
                      selectedProduct
                    )
                  }
                >
                  ♡ Wishlist
                </button>


                <button
                  className="modal-bag-btn"
                  onClick={() => {

                    handleAddToBag(
                      selectedProduct
                    );

                    setSelectedProduct(
                      null
                    );

                  }}
                >
                  🛍 Add to Bag
                </button>

              </div>

            </div>

          </div>

        </div>

      )}


      {/* =====================================================
          CHECKOUT
      ===================================================== */}

      {showCheckout && (

        <div
          className="checkout-overlay"
          onClick={
            closeCheckout
          }
        >

          <div
            className="checkout-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >


            {!orderPlaced ? (

              <>

                <div className="checkout-header">

                  <div>

                    <span>
                      RECOMAI CHECKOUT
                    </span>

                    <h2>
                      Complete your order
                    </h2>

                  </div>


                  <button
                    onClick={
                      closeCheckout
                    }
                  >
                    ×
                  </button>

                </div>


                <form
                  className="checkout-layout"
                  onSubmit={
                    handlePlaceOrder
                  }
                >


                  <div className="checkout-left">


                    <div className="checkout-section">

                      <div className="checkout-section-title">

                        <span>
                          01
                        </span>

                        <div>

                          <strong>
                            Delivery Details
                          </strong>

                          <small>
                            Where should we
                            deliver your order?
                          </small>

                        </div>

                      </div>


                      <div className="checkout-fields">


                        <div className="checkout-field">

                          <label>
                            Full Name
                          </label>

                          <input
                            name="name"
                            value={
                              checkoutData.name
                            }
                            onChange={
                              handleCheckoutChange
                            }
                            placeholder="Full name"
                          />

                        </div>


                        <div className="checkout-field">

                          <label>
                            Phone
                          </label>

                          <input
                            name="phone"
                            value={
                              checkoutData.phone
                            }
                            onChange={
                              handleCheckoutChange
                            }
                            placeholder="Phone number"
                          />

                        </div>


                        <div className="checkout-field full">

                          <label>
                            Address
                          </label>

                          <textarea
                            name="address"
                            value={
                              checkoutData.address
                            }
                            onChange={
                              handleCheckoutChange
                            }
                            placeholder="House no., street, area"
                            rows="3"
                          />

                        </div>


                        <div className="checkout-field">

                          <label>
                            City
                          </label>

                          <input
                            name="city"
                            value={
                              checkoutData.city
                            }
                            onChange={
                              handleCheckoutChange
                            }
                            placeholder="City"
                          />

                        </div>


                        <div className="checkout-field">

                          <label>
                            Pincode
                          </label>

                          <input
                            name="pincode"
                            value={
                              checkoutData.pincode
                            }
                            onChange={
                              handleCheckoutChange
                            }
                            placeholder="Pincode"
                          />

                        </div>

                      </div>

                    </div>


                    <div className="checkout-section">

                      <div className="checkout-section-title">

                        <span>
                          02
                        </span>

                        <div>

                          <strong>
                            Payment Method
                          </strong>

                          <small>
                            Choose payment
                          </small>

                        </div>

                      </div>


                      <div className="payment-options">


                        {[
                          [
                            "Cash on Delivery",
                            "💵",
                            "Pay when your order arrives",
                          ],

                          [
                            "UPI",
                            "📱",
                            "Google Pay, PhonePe, Paytm",
                          ],

                          [
                            "Card",
                            "💳",
                            "Credit / Debit Card",
                          ],
                        ].map(
                          (payment) => (

                            <label
                              key={
                                payment[0]
                              }
                              className={
                                checkoutData.payment ===
                                payment[0]
                                  ? "payment-option selected"
                                  : "payment-option"
                              }
                            >

                              <input
                                type="radio"
                                name="payment"
                                value={
                                  payment[0]
                                }
                                checked={
                                  checkoutData.payment ===
                                  payment[0]
                                }
                                onChange={
                                  handleCheckoutChange
                                }
                              />

                              <span className="payment-icon">
                                {
                                  payment[1]
                                }
                              </span>

                              <div>

                                <strong>
                                  {
                                    payment[0]
                                  }
                                </strong>

                                <small>
                                  {
                                    payment[2]
                                  }
                                </small>

                              </div>

                            </label>

                          )
                        )}

                      </div>

                    </div>

                  </div>


                  <div className="checkout-right">

                    <div className="order-summary">

                      <div className="summary-title">

                        <span>
                          YOUR ORDER
                        </span>

                        <strong>
                          {bag.length} items
                        </strong>

                      </div>


                      {bag.map(
                        (item) => (

                          <div
                            className="checkout-product"
                            key={
                              item.product_id
                            }
                          >

                            <div className="checkout-product-image">

                              {getImageUrl(
                                item
                              ) ? (

                                <img
                                  src={
                                    getImageUrl(
                                      item
                                    )
                                  }
                                  alt={
                                    item.title
                                  }
                                />

                              ) : (
                                <span>
                                  🛍
                                </span>
                              )}

                            </div>


                            <div className="checkout-product-info">

                              <strong>
                                {
                                  item.title
                                }
                              </strong>

                              <small>
                                Qty:{" "}
                                {
                                  item.quantity
                                }
                              </small>

                              <b>
                                {formatPrice(
                                  getProductPrice(
                                    item
                                  ) === null
                                    ? null
                                    : getProductPrice(
                                        item
                                      ) *
                                      Number(
                                        item.quantity ||
                                          1
                                      )
                                )}
                              </b>

                            </div>

                          </div>

                        )
                      )}


                      <div className="summary-line">

                        <span>
                          Subtotal
                        </span>

                        <strong>
                          {formatPrice(
                            bagTotal
                          )}
                        </strong>

                      </div>


                      <div className="summary-line">

                        <span>
                          Delivery
                        </span>

                        <strong className="free">
                          FREE
                        </strong>

                      </div>


                      <div className="summary-total">

                        <span>
                          Total
                        </span>

                        <strong>
                          {formatPrice(
                            bagTotal
                          )}
                        </strong>

                      </div>


                      <button
                        className="confirm-order-btn"
                        type="submit"
                      >
                        PLACE ORDER →
                      </button>

                    </div>

                  </div>

                </form>

              </>

            ) : (

              <div className="order-success">

                <div className="success-circle">
                  ✓
                </div>

                <span className="success-kicker">
                  ORDER CONFIRMED
                </span>

                <h2>
                  Your order is confirmed!
                </h2>

                <p>
                  Thank you{" "}
                  <strong>
                    {
                      checkoutData.name
                    }
                  </strong>
                  . Your order has been
                  successfully placed.
                </p>


                <div className="order-number">

                  <span>
                    ORDER ID
                  </span>

                  <strong>
                    #
                    {
                      lastOrder?.orderId
                    }
                  </strong>

                </div>


                <div className="success-details">

                  <div>

                    <span>
                      PAYMENT
                    </span>

                    <strong>
                      {
                        lastOrder?.payment
                      }
                    </strong>

                  </div>


                  <div>

                    <span>
                      TOTAL
                    </span>

                    <strong>
                      {formatPrice(
                        lastOrder?.total
                      )}
                    </strong>

                  </div>

                </div>


                <div className="success-actions">

                  <button
                    className="continue-shopping-btn"
                    onClick={() => {

                      closeCheckout();

                      window.scrollTo({
                        top: 0,
                        behavior:
                          "smooth",
                      });

                    }}
                  >
                    CONTINUE SHOPPING
                  </button>


                  <button
                    className="view-order-btn"
                    onClick={() => {

                      closeCheckout();

                      setActivePanel(
                        "orders"
                      );

                    }}
                  >
                    VIEW MY ORDERS
                  </button>

                </div>

              </div>

            )}

          </div>

        </div>

      )}


      {/* =====================================================
          FOOTER
      ===================================================== */}

      <footer className="footer">

        <div className="footer-brand">

          <strong>
            ✦ RecomAI
          </strong>

          <span>
            Multimodal E-Commerce
            Recommendation System
          </span>

        </div>

        <div className="footer-links">
          <strong>Explore</strong>
          <button onClick={() => document.getElementById("categories")?.scrollIntoView({ behavior: "smooth" })}>Shop categories</button>
          <button onClick={() => document.getElementById("ai-search")?.scrollIntoView({ behavior: "smooth" })}>AI-powered search</button>
          <button onClick={() => document.getElementById("how-ai-works")?.scrollIntoView({ behavior: "smooth" })}>How it works</button>
        </div>


        <div className="footer-tech">

          <span>
            React
          </span>

          <span>
            FastAPI
          </span>

          <span>
            ResNet50
          </span>

          <span>
            Sentence-BERT
          </span>

          <span>
            FAISS
          </span>

        </div>

      </footer>

    </div>
  );
}


export default App;
