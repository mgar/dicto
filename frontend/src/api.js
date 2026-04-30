const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export function localDateString(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function timezoneQuery(date = new Date()) {
  const params = new URLSearchParams({
    tz_offset: String(date.getTimezoneOffset()),
  });
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  if (timeZone) params.set("time_zone", timeZone);
  return params.toString();
}

export function timezonePayload(date = new Date()) {
  return {
    tz_offset: date.getTimezoneOffset(),
    time_zone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  };
}

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    credentials: "include" // critical for cookie sessions
  });

  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      detail = JSON.parse(text);
    } catch (_) {}
    const err = new Error(`API error ${res.status}`);
    err.status = res.status;
    err.detail = detail;
    throw err;
  }

  // some endpoints may return empty
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return await res.json();
  return null;
}
