const USER_ID_KEY = "multimodal_user_id";

export function getUserId() {
  return localStorage.getItem(USER_ID_KEY);
}

export function setUserId(userId) {
  localStorage.setItem(USER_ID_KEY, userId);
}

export function clearUserId() {
  localStorage.removeItem(USER_ID_KEY);
}

export async function createUser(apiFunction) {
  const existingUserId = getUserId();

  if (existingUserId) {
    return existingUserId;
  }

  const user = await apiFunction();

  if (!user?.user_id) {
    throw new Error("Backend did not return user_id");
  }

  setUserId(user.user_id);

  return user.user_id;
}