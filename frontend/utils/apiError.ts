import { isAxiosError } from "axios";

const FALLBACK_MESSAGE = "Something went wrong. Please try again.";

interface FastApiValidationError {
  msg?: string;
  message?: string;
  loc?: (string | number)[];
}

/**
 * Unwraps FastAPI's error response shape into a clean, user-displayable string.
 *
 * FastAPI errors typically come back as either:
 *   - `{"detail": "some string"}` (HTTPException, e.g. 401/404/409)
 *   - `{"detail": [{"msg": "...", "loc": [...]}, ...]}` (422 validation errors)
 *
 * Falls back to a generic message if the shape doesn't match either case.
 */
export function getApiErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string" && detail.trim().length > 0) {
      return detail;
    }

    if (Array.isArray(detail) && detail.length > 0) {
      const messages = detail
        .map((item: FastApiValidationError) => item?.msg ?? item?.message)
        .filter((msg): msg is string => typeof msg === "string" && msg.trim().length > 0);

      if (messages.length > 0) {
        return messages.join(", ");
      }
    }

    if (error.message) {
      return error.message;
    }
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return FALLBACK_MESSAGE;
}
