import { useEffect, useMemo, useState } from "react";
import { getPersonalizedRecommendations } from "../services/api";
import { getHistoryProfile, syncHistoryToBackend } from "../services/userHistory";
import ProductGrid from "./ProductGrid";

function localColdStart(catalog, query, category, history) {
  const excluded = new Set((history.events || []).filter((event) => event.product_id !== "__search__").map((event) => event.product_id));
  let products = catalog.filter((product) => !excluded.has(String(product.product_id)));
  if (category) products = products.filter((product) => (product.main_category || product.category) === category);

  const terms = String(query || "").toLowerCase().split(/\s+/).filter((term) => term.length > 1);
  if (terms.length) {
    const matching = products.filter((product) => {
      const searchable = `${product.title || ""} ${product.main_category || ""} ${product.store || ""} ${product.combined_text || ""}`.toLowerCase();
      return terms.some((term) => searchable.includes(term));
    });
    if (matching.length) products = matching;
  }

  return [...products]
    .sort((a, b) => Number(b.rating_number || 0) - Number(a.rating_number || 0) || Number(b.average_rating || 0) - Number(a.average_rating || 0))
    .slice(0, 12);
}

export default function PersonalizedRecommendations({
  activityVersion = 0,
  query = "",
  category = "",
  catalog = [],
  catalogLoading = false,
  wishlist = [],
  bag = [],
  onWishlist,
  onAddToBag,
  onViewDetails,
}) {
  const [recommendations, setRecommendations] = useState([]);
  const [becauseViewed, setBecauseViewed] = useState([]);
  const [basedOnInterests, setBasedOnInterests] = useState([]);
  const [coldStart, setColdStart] = useState(true);
  const [serviceUnavailable, setServiceUnavailable] = useState(false);
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState({ distinctProductCount: 0, viewed: [], top_categories: [] });

  const localPopular = useMemo(
    () => localColdStart(catalog, query, category, profile),
    [catalog, query, category, profile],
  );

  useEffect(() => {
    let active = true;
    const load = async () => {
      setLoading(true);
      const currentProfile = getHistoryProfile();
      if (active) setProfile(currentProfile);
      try {
        const userId = await syncHistoryToBackend();
        const data = await getPersonalizedRecommendations(userId, 10, { query, category });
        if (!active) return;
        setProfile({
          ...currentProfile,
          ...(data.profile || {}),
          distinctProductCount: data.profile?.distinct_product_count ?? currentProfile.distinctProductCount,
        });
        setRecommendations(data.recommendations || []);
        setBecauseViewed(data.because_viewed || []);
        setBasedOnInterests(data.based_on_interests || []);
        setColdStart(Boolean(data.cold_start));
        setServiceUnavailable(false);
      } catch {
        if (!active) return;
        const isNewProfile = currentProfile.distinctProductCount < 3;
        setRecommendations(isNewProfile ? localColdStart(catalog, query, category, currentProfile) : []);
        setBecauseViewed([]);
        setBasedOnInterests([]);
        setColdStart(isNewProfile);
        setServiceUnavailable(!isNewProfile);
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => { active = false; };
  }, [activityVersion, query, category, catalog]);

  const primaryProducts = serviceUnavailable || !coldStart
    ? recommendations
    : recommendations.length ? recommendations : localPopular;
  const onGridProps = { wishlist, bag, onWishlist, onAddToBag, onViewDetails };
  const emptyWhileLoading = loading && !primaryProducts.length;

  return (
    <section className="personalization-home" id="personalized-recommendations" aria-labelledby="personalized-title">
      <div className="personalization-title-row">
        <div>
          <span className="section-label">A PERSONAL STYLE EDIT</span>
          <h2 id="personalized-title">Recommended For You</h2>
          <p>{coldStart ? "Popular, highly rated finds while we learn what you like." : `Based on ${profile.distinctProductCount || "your"} products you've interacted with.`}</p>
        </div>
        <span className={`personalization-mode ${coldStart ? "is-cold" : "is-personalized"}`}>
          {loading ? "UPDATING" : coldStart ? "POPULAR PICKS" : "YOUR INTERESTS"}
        </span>
      </div>
      {emptyWhileLoading ? <div className="personalization-empty">Finding products for you…</div> : primaryProducts.length ? <ProductGrid products={primaryProducts} {...onGridProps} className="personalized-grid" /> : serviceUnavailable ? <div className="personalization-empty">History based recommendations are temporarily unavailable. Your activity is saved on this device and will sync when the recommendation service is available.</div> : !catalogLoading && <div className="personalization-empty">Popular picks will appear when the product catalog is available.</div>}

      <div className="personalization-secondary-grid">
        <section className="personalization-subsection" aria-labelledby="because-viewed-title">
          <div className="personalization-subheading">
            <div><span className="section-label">PICKING UP WHERE YOU LEFT OFF</span><h3 id="because-viewed-title">Because you viewed…</h3></div>
          </div>
          {becauseViewed.length ? <ProductGrid products={becauseViewed.slice(0, 4)} {...onGridProps} className="personalized-grid personalized-compact-grid" /> : <p className="personalization-hint">{profile.viewed?.length ? "Related picks will appear as soon as the recommendation service is available." : "Open a product to get similar finds here."}</p>}
        </section>

        <section className="personalization-subsection" aria-labelledby="interests-title">
          <div className="personalization-subheading">
            <div><span className="section-label">A BETTER FIT WITH EVERY VISIT</span><h3 id="interests-title">Based on your interests…</h3></div>
          </div>
          {basedOnInterests.length ? <ProductGrid products={basedOnInterests.slice(0, 4)} {...onGridProps} className="personalized-grid personalized-compact-grid" /> : <p className="personalization-hint">{coldStart ? `Interact with ${Math.max(0, 3 - (profile.distinctProductCount || 0))} more distinct products to build your interest profile.` : "Your interest-based picks are updating."}</p>}
        </section>
      </div>
      {profile.top_categories?.length > 0 && <div className="interest-tags" aria-label="Your top interests">{profile.top_categories.map((item) => <span key={item}>{item}</span>)}</div>}
    </section>
  );
}
