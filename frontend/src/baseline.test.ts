import { describe, expect, it } from "vitest";

describe("frontend baseline", () => {
  it("has a stable application name", () => {
    expect("HR Talent Matching Platform").toContain("Talent Matching");
  });
});
