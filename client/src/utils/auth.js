export const validateToken = () => {
  const token = localStorage.getItem("access_token");
  if (!token) return false;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const expiry = payload.exp * 1000;
    if (Date.now() >= expiry) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("username");
      return false;
    }
    return true;
  } catch (e) {
    return false;
  }
};
