const API_BASE_URL =import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8081";
export async function sendChatMessage(message, history = []) {
  const safeHistory = history
    .filter((item) => item.role === "user" || item.role === "assistant")
    .map((item) => ({ role: item.role, content: item.content }));

  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      history: safeHistory,
      top_k: 3,
    }),
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || "Failed to get response from AgroGuard.");
  }

  return data;
}
