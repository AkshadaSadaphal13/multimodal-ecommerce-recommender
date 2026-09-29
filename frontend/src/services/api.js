import axios from "axios";

const API_BASE_URL =
 import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});


/* =========================================================
   TEXT SEARCH
========================================================= */

export async function getRecommendations(
  query,
  topK = 10,
  filters = {}
) {
  const response = await api.post(
    "/api/recommend",
    {
      query,
      top_k: topK,

      category:
        filters.category || null,

      min_rating:
        filters.minRating !== ""
          ? Number(filters.minRating)
          : null,

      max_price:
        filters.maxPrice !== ""
          ? Number(filters.maxPrice)
          : null,
    }
  );

  return response.data;
}


/* =========================================================
   IMAGE SEARCH
========================================================= */

export async function getImageRecommendations(
  image,
  topK = 10,
  filters = {}
) {
  const formData = new FormData();

  formData.append(
    "image",
    image
  );

  formData.append(
    "top_k",
    String(topK)
  );

  if (filters.category) {
    formData.append(
      "category",
      filters.category
    );
  }

  if (
    filters.minRating !== "" &&
    filters.minRating !== null &&
    filters.minRating !== undefined
  ) {
    formData.append(
      "min_rating",
      String(filters.minRating)
    );
  }

  if (
    filters.maxPrice !== "" &&
    filters.maxPrice !== null &&
    filters.maxPrice !== undefined
  ) {
    formData.append(
      "max_price",
      String(filters.maxPrice)
    );
  }

  const response = await api.post(
    "/api/recommend/image",
    formData,
    {
      headers: {
        "Content-Type":
          "multipart/form-data",
      },
    }
  );

  return response.data;
}


/* =========================================================
   TEXT + IMAGE MULTIMODAL SEARCH
========================================================= */

export async function getMultimodalRecommendations(
  query,
  image,
  topK = 10,
  filters = {},
  textWeight = 0.5,
  imageWeight = 0.5
) {
  const formData = new FormData();

  formData.append(
    "query",
    query || ""
  );

  formData.append(
    "image",
    image
  );

  formData.append(
    "top_k",
    String(topK)
  );

  formData.append(
    "text_weight",
    String(textWeight)
  );

  formData.append(
    "image_weight",
    String(imageWeight)
  );

  if (filters.category) {
    formData.append(
      "category",
      filters.category
    );
  }

  if (
    filters.minRating !== "" &&
    filters.minRating !== null &&
    filters.minRating !== undefined
  ) {
    formData.append(
      "min_rating",
      String(filters.minRating)
    );
  }

  if (
    filters.maxPrice !== "" &&
    filters.maxPrice !== null &&
    filters.maxPrice !== undefined
  ) {
    formData.append(
      "max_price",
      String(filters.maxPrice)
    );
  }

  const response = await api.post(
    "/api/recommend/multimodal",
    formData,
    {
      headers: {
        "Content-Type":
          "multipart/form-data",
      },
    }
  );

  return response.data;
}


/* =========================================================
   PRODUCTS
========================================================= */

export async function getProducts() {
  const response = await api.get(
    "/products"
  );

  return response.data;
}


/* =========================================================
   HEALTH CHECK
========================================================= */

export async function checkBackendHealth() {
  const response = await api.get(
    "/health"
  );

  return response.data;
}


export default api;