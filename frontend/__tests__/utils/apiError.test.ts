import { describe, it, expect } from "vitest";
import { AxiosError } from "axios";
import { getApiErrorMessage } from "@/utils/apiError";

function makeAxiosError(data: unknown, status = 400): AxiosError {
  const error = new AxiosError("Request failed");
  error.response = {
    data,
    status,
    statusText: "Bad Request",
    headers: {},
    // @ts-expect-error minimal config for test purposes
    config: {},
  };
  return error;
}

describe("getApiErrorMessage", () => {
  it("unwraps a string detail (HTTPException shape)", () => {
    const error = makeAxiosError({ detail: "Invalid credentials" }, 401);
    expect(getApiErrorMessage(error)).toBe("Invalid credentials");
  });

  it("unwraps a 422 validation error array shape and joins messages", () => {
    const error = makeAxiosError(
      {
        detail: [
          { loc: ["body", "email"], msg: "field required" },
          { loc: ["body", "password"], msg: "field required" },
        ],
      },
      422
    );
    expect(getApiErrorMessage(error)).toBe("field required, field required");
  });

  it("falls back to a generic message when the shape is unrecognized", () => {
    const error = makeAxiosError({}, 500);
    // AxiosError still has a generic `message`, so it should surface that
    // rather than a hardcoded fallback in this case.
    expect(getApiErrorMessage(error)).toBe("Request failed");
  });

  it("falls back to a generic message for a completely unknown error shape", () => {
    expect(getApiErrorMessage("just a string")).toBe(
      "Something went wrong. Please try again."
    );
    expect(getApiErrorMessage(null)).toBe("Something went wrong. Please try again.");
    expect(getApiErrorMessage(undefined)).toBe(
      "Something went wrong. Please try again."
    );
  });

  it("uses a native Error's message when not an axios error", () => {
    expect(getApiErrorMessage(new Error("boom"))).toBe("boom");
  });
});
