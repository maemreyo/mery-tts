import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { useSession } from "../useSession";

const STORAGE_KEY = "mery.console.authToken";

afterEach(() => {
  localStorage.clear();
});

describe("useSession", () => {
  it("reads initial session from localStorage when token is stored", () => {
    localStorage.setItem(STORAGE_KEY, "stored-token");
    const { result } = renderHook(() => useSession());
    expect(result.current.session.token).toBe("stored-token");
    expect(result.current.session.remember).toBe(true);
  });

  it("starts with empty session when nothing is stored", () => {
    const { result } = renderHook(() => useSession());
    expect(result.current.session.token).toBe("");
    expect(result.current.session.remember).toBe(false);
  });

  it("persists token when remember is true", async () => {
    const { result } = renderHook(() => useSession());
    act(() => {
      result.current.applyToken("new-token", true);
    });
    expect(result.current.session.token).toBe("new-token");
    expect(result.current.session.remember).toBe(true);
    expect(localStorage.getItem(STORAGE_KEY)).toBe("new-token");
  });

  it("does not persist token when remember is false", async () => {
    const { result } = renderHook(() => useSession());
    act(() => {
      result.current.applyToken("new-token", false);
    });
    expect(result.current.session.token).toBe("new-token");
    expect(result.current.session.remember).toBe(false);
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it("clears session and localStorage on logout", () => {
    localStorage.setItem(STORAGE_KEY, "remembered-token");
    const { result } = renderHook(() => useSession());
    act(() => {
      result.current.logout();
    });
    expect(result.current.session.token).toBe("");
    expect(result.current.session.remember).toBe(false);
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });
});
