import { describe, expect, it, vi } from "vitest";
import { dashboardMetrics, request, validateUpload } from "./api";

describe("delivery coverage", () => {
  it("rejects empty and oversized uploads", () => {
    expect(validateUpload(new File([], "empty.txt", { type: "text/plain" }))).toContain("between");
    expect(validateUpload(new File([new Uint8Array(10 * 1024 * 1024 + 1)], "large.txt"))).toContain("between");
  });

  it("surfaces API validation errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Forbidden" }), { status: 403 })));
    await expect(request("/admin", { tenantId: "tenant-a", role: "Viewer", accessToken: null })).rejects.toThrow("Forbidden");
    vi.unstubAllGlobals();
  });

  it("keeps processing and result counts tenant-local at the view boundary", () => {
    expect(dashboardMetrics([{ status: "queued" }, { status: "ready" }], [{ id: "job" }], [])).toEqual({
      employees: 1,
      jobs: 1,
      matches: 0,
      processing: 1,
    });
  });
});
