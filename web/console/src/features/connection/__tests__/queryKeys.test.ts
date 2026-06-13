import { QUERY_KEYS } from "@shared/api/queryKeys";
import { describe, expect, it } from "vitest";

describe("QUERY_KEYS stability", () => {
  it("health key is stable for the same token", () => {
    const a = QUERY_KEYS.health("tok-123");
    const b = QUERY_KEYS.health("tok-123");
    expect(a).toEqual(b);
    expect(a[0]).toBe("health");
    expect(a[1]).toBe("tok-123");
  });

  it("health key differs for different tokens", () => {
    const a = QUERY_KEYS.health("tok-aaa");
    const b = QUERY_KEYS.health("tok-bbb");
    expect(a).not.toEqual(b);
  });

  it("voices key is stable for the same token", () => {
    const a = QUERY_KEYS.voices("tok-123");
    const b = QUERY_KEYS.voices("tok-123");
    expect(a).toEqual(b);
    expect(a[0]).toBe("voices");
  });

  it("health and voices keys for same token are distinct", () => {
    const h = QUERY_KEYS.health("tok");
    const v = QUERY_KEYS.voices("tok");
    expect(h).not.toEqual(v);
  });
});
