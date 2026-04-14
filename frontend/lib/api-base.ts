const LOCAL_API_ORIGIN = "http://localhost:8000";
const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "0.0.0.0"]);

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim() ?? "";

  if (typeof window === "undefined") {
    if (configured) {
      return trimTrailingSlash(configured);
    }
    return process.env.NODE_ENV === "development" ? LOCAL_API_ORIGIN : "";
  }

  if (!configured) {
    return process.env.NODE_ENV === "development" ? LOCAL_API_ORIGIN : "";
  }

  try {
    const resolved = new URL(configured, window.location.origin);
    const isLocalHttpTarget =
      resolved.protocol === "http:" && LOCAL_HOSTS.has(resolved.hostname);

    // On HTTPS pages, fall back to same-origin requests if the configured API URL
    // would trigger mixed content or violate connect-src 'self'.
    if (
      window.location.protocol === "https:" &&
      resolved.protocol === "http:" &&
      !isLocalHttpTarget
    ) {
      return "";
    }

    if (resolved.origin === window.location.origin) {
      return "";
    }

    return trimTrailingSlash(resolved.toString());
  } catch {
    return trimTrailingSlash(configured);
  }
}

export function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${getApiBaseUrl()}${normalizedPath}`;
}
