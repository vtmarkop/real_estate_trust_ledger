import { translateText } from "./i18n.js";

export function ApiError(message, status, details) {
  this.name = "ApiError";
  this.message =
    typeof message === "string" && message.trim()
      ? translateText(message)
      : translateText("Request failed.");
  this.status = status;
  this.details = details || null;
}

ApiError.prototype = Object.create(Error.prototype);
ApiError.prototype.constructor = ApiError;

function getRuntimeEnv() {
  if (typeof import.meta !== "undefined" && import.meta.env) {
    return import.meta.env;
  }
  return {};
}

export function formatApiErrorMessage(detail) {
  if (detail == null) {
    return "";
  }

  if (typeof detail === "string") {
    return translateText(detail.trim());
  }

  if (Array.isArray(detail)) {
    return detail
      .map(formatApiErrorMessage)
      .filter(Boolean)
      .join("; ");
  }

  if (typeof detail === "object") {
    if (typeof detail.msg === "string") {
      var location = Array.isArray(detail.loc) ? detail.loc.join(" > ") : "";
      return translateText(location ? location + ": " + detail.msg : detail.msg);
    }

    if (typeof detail.message === "string") {
      return translateText(detail.message.trim());
    }

    if (detail.detail != null) {
      return formatApiErrorMessage(detail.detail);
    }

    try {
      return JSON.stringify(detail);
    } catch (error) {
      return translateText("Request failed.");
    }
  }

  return translateText(String(detail));
}

var runtimeEnv = getRuntimeEnv();
var apiBaseUrl = (runtimeEnv.VITE_TRUST_LEDGER_API_BASE_URL || "").replace(/\/$/, "");
export var API_PREFIX = (apiBaseUrl ? apiBaseUrl : "") + "/api/v1";

async function parseResponseBody(response) {
  if (response.status === 204) {
    return null;
  }

  var contentType = response.headers.get("content-type") || "";
  if (contentType.indexOf("application/json") !== -1) {
    return response.json();
  }

  var text = await response.text();
  return text || null;
}

export async function apiRequest(path, options) {
  var requestOptions = options || {};
  var headers = Object.assign({}, requestOptions.headers || {});
  var body = requestOptions.body;

  if (
    body &&
    typeof body === "object" &&
    !(body instanceof FormData) &&
    !headers["Content-Type"]
  ) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(body);
  }

  var response = await fetch(API_PREFIX + path, {
    method: requestOptions.method || "GET",
    credentials: "include",
    headers: headers,
    body: body
  });

  var payload = await parseResponseBody(response);

  if (!response.ok) {
    var message = translateText("Request failed.");
    if (payload && typeof payload === "object" && payload.detail) {
      message = formatApiErrorMessage(payload.detail) || message;
    } else if (typeof payload === "string" && payload.trim()) {
      message = translateText(payload.trim());
    } else if (payload && typeof payload === "object") {
      message = formatApiErrorMessage(payload) || message;
    }
    throw new ApiError(message, response.status, payload);
  }

  return payload;
}
