const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";


// ============================================================
// HELPER — READ API ERROR
// ============================================================

async function getErrorMessage(response, fallbackMessage) {
  try {
    const data = await response.json();

    if (data?.detail) {
      if (typeof data.detail === "string") {
        return data.detail;
      }

      return JSON.stringify(data.detail);
    }

    if (data?.message) {
      return data.message;
    }
  } catch {
    // Ignore JSON parsing errors
  }

  try {
    const text = await response.text();

    if (text) {
      return text;
    }
  } catch {
    // Ignore text parsing errors
  }

  return fallbackMessage;
}


// ============================================================
// HEALTH
// ============================================================

export async function checkBackendHealth() {
  const response = await fetch(
    `${API_BASE_URL}/health`
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Backend is not healthy"
      )
    );
  }

  return response.json();
}


// ============================================================
// NORMAL TEXT RECOMMENDATION
// ============================================================

export async function getRecommendations(
  query,
  topK = 10,
  filters = {}
) {
  const body = {
    query: String(query || "").trim(),
    top_k: Number(topK),
  };

  // Optional filters
  if (
    filters.category !== undefined &&
    filters.category !== ""
  ) {
    body.category = filters.category;
  }

  if (
    filters.minRating !== undefined &&
    filters.minRating !== ""
  ) {
    body.min_rating =
      Number(filters.minRating);
  }

  if (
    filters.maxPrice !== undefined &&
    filters.maxPrice !== ""
  ) {
    body.max_price =
      Number(filters.maxPrice);
  }

  const response = await fetch(
    `${API_BASE_URL}/api/recommend`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify(body),
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to get recommendations"
      )
    );
  }

  return response.json();
}


// ============================================================
// IMAGE RECOMMENDATION
// ============================================================

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

  if (
    filters.category !== undefined &&
    filters.category !== ""
  ) {
    formData.append(
      "category",
      filters.category
    );
  }

  if (
    filters.minRating !== undefined &&
    filters.minRating !== ""
  ) {
    formData.append(
      "min_rating",
      String(filters.minRating)
    );
  }

  if (
    filters.maxPrice !== undefined &&
    filters.maxPrice !== ""
  ) {
    formData.append(
      "max_price",
      String(filters.maxPrice)
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/api/recommend/image`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to get image recommendations"
      )
    );
  }

  return response.json();
}


// ============================================================
// MULTIMODAL RECOMMENDATION
// ============================================================

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

  if (
    filters.category !== undefined &&
    filters.category !== ""
  ) {
    formData.append(
      "category",
      filters.category
    );
  }

  if (
    filters.minRating !== undefined &&
    filters.minRating !== ""
  ) {
    formData.append(
      "min_rating",
      String(filters.minRating)
    );
  }

  if (
    filters.maxPrice !== undefined &&
    filters.maxPrice !== ""
  ) {
    formData.append(
      "max_price",
      String(filters.maxPrice)
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/api/recommend/multimodal`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to get multimodal recommendations"
      )
    );
  }

  return response.json();
}


// ============================================================
// PRODUCTS
// ============================================================

export async function getProducts(limit = 2500) {
  const response = await fetch(
    `${API_BASE_URL}/api/products/?limit=${encodeURIComponent(limit)}`
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to fetch products"
      )
    );
  }

  return response.json();
}


// ============================================================
// CREATE USER
// ============================================================

export async function createUser(name = null, email = null, userId = null) {
  const response = await fetch(
    `${API_BASE_URL}/api/users`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({ name, email, user_id: userId }),
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to create user"
      )
    );
  }

  return response.json();
}


// ============================================================
// SAVE USER PREFERENCES
// ============================================================

export async function saveUserPreferences(
  userId,
  categories,
  minPrice = 0,
  maxPrice = null
) {
  const response = await fetch(
    `${API_BASE_URL}/api/users/${userId}/preferences`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        categories,

        min_price:
          Number(minPrice || 0),

        max_price:
          maxPrice === "" ||
          maxPrice === null ||
          maxPrice === undefined
            ? null
            : Number(maxPrice),
      }),
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to save user preferences"
      )
    );
  }

  return response.json();
}


// ============================================================
// RECORD USER HISTORY
// ============================================================

export async function recordUserHistory(
  userId,
  productId,
  eventType,
  query = null,
  eventId = null
) {
  const response = await fetch(
    `${API_BASE_URL}/api/users/${userId}/history`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        product_id:
          String(productId),

        event_type:
          eventType,

        event_id:
          eventId,

        query,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to record user history"
      )
    );
  }

  return response.json();
}


// ============================================================
// GET USER HISTORY
// ============================================================

export async function getUserHistory(
  userId
) {
  const response = await fetch(
    `${API_BASE_URL}/api/users/${userId}/history`
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to get user history"
      )
    );
  }

  return response.json();
}


// ============================================================
// GET USER PROFILE
// ============================================================

export async function getUserProfile(
  userId
) {
  const response = await fetch(
    `${API_BASE_URL}/api/users/${userId}/profile`
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to get user profile"
      )
    );
  }

  return response.json();
}


// ============================================================
// PERSONALIZED RECOMMENDATIONS
// ============================================================

export async function getPersonalizedRecommendations(
  userId,
  topK = 10,
  context = {}
) {
  const params = new URLSearchParams({ top_k: String(topK) });
  if (context.query) params.set("query", context.query);
  if (context.category) params.set("category", context.category);
  const response = await fetch(
    `${API_BASE_URL}/api/users/${userId}/recommendations?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to get personalized recommendations"
      )
    );
  }

  return response.json();
}


// ============================================================
// API BASE URL
// ============================================================

export { API_BASE_URL };
