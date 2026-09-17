import { describe, expect, it, vi } from "vitest";
import { dashboardMetrics, request, validateUpload } from "./api";
import { navigation } from "./workspace";

describe("frontend baseline", () => {
  it("has a stable application name", () => {
    expect("HR Talent Matching Platform").toContain("Talent Matching");
  });

  it("exposes the shared workspace views and hides admin navigation for non-admins", () => {
    const role: string = "Recruiter";
    expect(navigation.map((item) => item.id)).toEqual(["dashboard", "resumes", "jobs", "matching", "chat", "admin"]);
    expect(navigation.filter((item) => !item.adminOnly || role === "HR Admin").map((item) => item.id)).toEqual(["dashboard", "resumes", "jobs", "matching", "chat"]);
  });

  it("validates supported upload states", () => {
    expect(validateUpload(null)).toBe("Choose a PDF, DOCX, or TXT file.");
    expect(validateUpload(new File(["resume"], "resume.exe", { type: "application/octet-stream" }))).toContain("Only PDF");
    expect(validateUpload(new File(["resume"], "resume.pdf", { type: "application/pdf" }))).toBeNull();
  });

  it("derives tenant-scoped dashboard counts", () => {
    expect(dashboardMetrics([{ status: "ready" }, { status: "processing" }, { status: "failed" }], [{ id: 1 }], [{ id: 2 }])).toEqual({ employees: 1, jobs: 1, matches: 1, processing: 1 });
  });

  it("sends session scope and role with API requests", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 })));
    await request("/health", { tenantId: "tenant-b", role: "Viewer", accessToken: "token" });
    const [, init] = vi.mocked(fetch).mock.calls[0];
    expect(new Headers(init?.headers).get("X-Tenant-ID")).toBe("tenant-b");
    expect(new Headers(init?.headers).get("X-Role")).toBe("Viewer");
    expect(new Headers(init?.headers).get("Authorization")).toBe("Bearer token");
    vi.unstubAllGlobals();
  });
});
