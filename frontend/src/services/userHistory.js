import { createUser as createBackendUser, recordUserHistory } from "./api";
import { getUserId, setUserId } from "../utils/userSession";

export const PERSONALIZATION_STORAGE_KEY = "recomai_personalization_v1";
const MAX_EVENTS = 500;
let syncInFlight = null;

function makeId() {
  return globalThis.crypto?.randomUUID?.() || `evt_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function readRawState() {
  try {
    const saved = JSON.parse(localStorage.getItem(PERSONALIZATION_STORAGE_KEY) || "null");
    if (saved?.version === 1 && Array.isArray(saved.events)) return saved;
  } catch { /* Recover cleanly from invalid local data. */ }
  return { version: 1, profileId: makeId(), events: [], updatedAt: new Date().toISOString() };
}

function compactProduct(product) {
  if (!product || typeof product !== "object") return null;
  return {
    product_id: String(product.product_id || ""),
    title: product.title || "",
    main_category: product.main_category || product.category || "",
    average_rating: product.average_rating ?? product.rating ?? null,
    rating_number: product.rating_number ?? null,
    price: product.price ?? null,
    image_url: product.image_url || product.image || "",
    store: product.store || product.brand || "",
  };
}

function persist(state) {
  state.updatedAt = new Date().toISOString();
  localStorage.setItem(PERSONALIZATION_STORAGE_KEY, JSON.stringify(state));
  return state;
}

function migrateLegacyActivity(state) {
  if (state.migratedLegacy) return state;
  const addLegacy = (items, type) => {
    for (const product of items) {
      if (!product?.product_id) continue;
      if (state.events.some((event) => event.type === type && event.product_id === String(product.product_id))) continue;
      state.events.push({ event_id: makeId(), type, product_id: String(product.product_id), product: compactProduct(product), query: null, category: product.main_category || product.category || null, timestamp: new Date().toISOString(), synced: false });
    }
  };
  try { addLegacy(JSON.parse(localStorage.getItem("recomai_recently_viewed") || "[]"), "view"); } catch { /* Ignore malformed legacy state. */ }
  try { addLegacy(JSON.parse(localStorage.getItem("recomai_wishlist") || "[]"), "wishlist"); } catch { /* Ignore malformed legacy state. */ }
  try { addLegacy(JSON.parse(localStorage.getItem("recomai_bag") || "[]"), "cart"); } catch { /* Ignore malformed legacy state. */ }
  state.migratedLegacy = true;
  state.events = state.events.slice(-MAX_EVENTS);
  return persist(state);
}

export function getHistorySnapshot() {
  return migrateLegacyActivity(readRawState());
}

function storeActivity({ type, product = null, query = null, category = null }) {
  const state = migrateLegacyActivity(readRawState());
  const productSummary = compactProduct(product);
  const event = {
    event_id: makeId(),
    type,
    product_id: productSummary?.product_id || (type === "search" ? "__search__" : ""),
    product: productSummary,
    query: query ? String(query).trim().slice(0, 500) : null,
    category: category || productSummary?.main_category || null,
    timestamp: new Date().toISOString(),
    synced: false,
  };
  if (!event.product_id) return state;
  state.events = [...state.events, event].slice(-MAX_EVENTS);
  persist(state);
  return state;
}

export async function syncHistoryToBackend() {
  if (syncInFlight) return syncInFlight;
  syncInFlight = (async () => {
    let userId = getUserId();
    if (!userId) {
      const user = await createBackendUser();
      userId = user?.user_id;
      if (!userId) throw new Error("Personalization user could not be created");
      setUserId(userId);
    }

    let state = getHistorySnapshot();
    for (const event of state.events) {
      if (event.synced) continue;
      await recordUserHistory(userId, event.product_id, event.type, event.query, event.event_id);
      state = getHistorySnapshot();
      const synced = state.events.map((item) => item.event_id === event.event_id ? { ...item, synced: true } : item);
      persist({ ...state, events: synced });
    }
    return userId;
  })();
  try { return await syncInFlight; }
  finally { syncInFlight = null; }
}

export function trackActivity(activity) {
  const state = storeActivity(activity);
  void syncHistoryToBackend().catch(() => { /* Browser history stays available while the API is offline. */ });
  return Promise.resolve(state);
}

export function getHistoryProfile() {
  const state = getHistorySnapshot();
  const categoryWeights = {};
  const counts = state.events.reduce((result, event) => {
    result[event.type] = (result[event.type] || 0) + 1;
    const category = event.product?.main_category;
    if (category) {
      const weight = { view: 1, wishlist: 3, cart: 4, purchase: 5 }[event.type] || 0;
      categoryWeights[category] = (categoryWeights[category] || 0) + weight;
    }
    return result;
  }, {});
  const viewed = state.events.filter((event) => event.type === "view" && event.product);
  const distinctProducts = new Set(state.events.filter((event) => event.product_id && event.product_id !== "__search__").map((event) => event.product_id));
  const top_categories = Object.keys(categoryWeights).sort((a, b) => categoryWeights[b] - categoryWeights[a]).slice(0, 5);
  return { ...state, counts, viewed, top_categories, distinctProductCount: distinctProducts.size };
}

