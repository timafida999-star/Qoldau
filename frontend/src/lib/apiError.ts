/**
 * Extract a human-readable message from an Axios error.
 *
 * FastAPI returns `detail` as a string for our own HTTPExceptions, but as an
 * ARRAY of objects for validation errors (422). Rendering that array as a
 * React child crashes the whole tree, so anything non-string falls back to the
 * caller's message.
 */
export function apiErrorMessage(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === "string" && detail.trim() ? detail : fallback;
}
