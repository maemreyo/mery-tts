import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { healthReadyV2, storageWarn } from "../../../test/fixtures/health";
import { server } from "../../../test/handlers";
import { renderWithProviders } from "../../../test/renderWithProviders";
import { HealthPanel } from "../HealthPanel";

describe("HealthPanel", () => {
  it("renders backend-owned readiness data when ready", async () => {
    renderWithProviders(<HealthPanel token="test-token" />);
    await waitFor(() => expect(screen.getByText("Ready")).toBeInTheDocument());
    expect(screen.getByText("ok")).toBeInTheDocument();
    expect(
      screen.getByText("Live status — refreshes every 30 s."),
    ).toBeInTheDocument();
  });

  it("shows no-token state with Go to Overview button when token is empty", () => {
    renderWithProviders(<HealthPanel token="" />);
    expect(screen.getByText("Enter a bearer token above.")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Go to Overview" }),
    ).toBeInTheDocument();
  });

  it("navigates to overview when Go to Overview is clicked in no-token state", async () => {
    const user = userEvent.setup();
    renderWithProviders(<HealthPanel token="" />);
    const btn = screen.getByRole("button", { name: "Go to Overview" });
    await user.click(btn);
    // NavigationProvider updates globalThis.location.hash
    expect(globalThis.location.hash).toBe("#overview");
  });

  it("shows error/unreachable state with recovery buttons when server is not reachable", async () => {
    server.use(http.get("/v1/health", () => HttpResponse.error()));
    renderWithProviders(<HealthPanel token="test-token" />);
    await waitFor(() =>
      expect(
        screen.getByText(
          "Cannot reach the Mery server. Is mery serve running?",
        ),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("button", { name: "Go to Overview" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Open Developer Mode" }),
    ).toBeInTheDocument();
  });

  it("shows not-ready state with diagnostics link when server is reachable but not ready", async () => {
    server.use(
      http.get("/v1/health", () =>
        HttpResponse.json({
          schema_version: "v1",
          ready: false,
          health_status: "degraded",
          total_usable_voices: 0,
        }),
      ),
    );
    renderWithProviders(<HealthPanel token="test-token" />);
    await waitFor(() =>
      expect(
        screen.getByText("Server is running but not ready."),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText("degraded")).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "Open Developer Mode for diagnostics",
      }),
    ).toBeInTheDocument();
  });

  it("health section has role=region and aria-label=Health", async () => {
    renderWithProviders(<HealthPanel token="test-token" />);
    await waitFor(() => expect(screen.getByText("Ready")).toBeInTheDocument());
    const region = screen.getByRole("region", { name: "Health" });
    expect(region).toBeInTheDocument();
  });

  it("health section has role=region in no-token state", () => {
    renderWithProviders(<HealthPanel token="" />);
    const region = screen.getByRole("region", { name: "Health" });
    expect(region).toBeInTheDocument();
  });

  // ─── Engine health grid ──────────────────────────────────────────────────

  it("renders engine cards for each engine in data.engines", async () => {
    renderWithProviders(<HealthPanel token="test-token" />);
    await waitFor(() => expect(screen.getByText("Ready")).toBeInTheDocument());
    // Default fixture has two engines: kokoro (available) and espeak (degraded)
    expect(screen.getByText("kokoro")).toBeInTheDocument();
    expect(screen.getByText("espeak")).toBeInTheDocument();
    // Status badges
    expect(screen.getByText("available")).toBeInTheDocument();
    expect(screen.getByText("degraded")).toBeInTheDocument();
  });

  it("shows degraded engine reason text", async () => {
    renderWithProviders(<HealthPanel token="test-token" />);
    await waitFor(() => expect(screen.getByText("Ready")).toBeInTheDocument());
    expect(screen.getByText("Smoke test failed")).toBeInTheDocument();
  });

  it("skips engine section when engines array is empty", async () => {
    server.use(
      http.get("/v1/health", () =>
        HttpResponse.json({ ...healthReadyV2, engines: [] }),
      ),
    );
    renderWithProviders(<HealthPanel token="test-token" />);
    await waitFor(() => expect(screen.getByText("Ready")).toBeInTheDocument());
    expect(screen.queryByText("Engine Status")).not.toBeInTheDocument();
  });

  // ─── Storage section ─────────────────────────────────────────────────────

  it("renders storage breakdown with formatted bytes", async () => {
    renderWithProviders(<HealthPanel token="test-token" />);
    await waitFor(() => expect(screen.getByText("Ready")).toBeInTheDocument());
    // Storage query is enabled once health is connected
    await waitFor(() =>
      expect(screen.getByText("Total used")).toBeInTheDocument(),
    );
    // 52_428_800 bytes = 50.0 MB
    expect(screen.getByText("50.0 MB")).toBeInTheDocument();
  });

  it("shows advisory warning banner when storage advisory status is warn", async () => {
    server.use(http.get("/v1/storage", () => HttpResponse.json(storageWarn)));
    renderWithProviders(<HealthPanel token="test-token" />);
    await waitFor(() => expect(screen.getByText("Ready")).toBeInTheDocument());
    await waitFor(() =>
      expect(
        screen.getByText(
          "Storage is running low. Consider cleaning up cache and logs.",
        ),
      ).toBeInTheDocument(),
    );
  });

  it("renders cleanup buttons for cache, logs, diagnostics but not models", async () => {
    renderWithProviders(<HealthPanel token="test-token" />);
    await waitFor(() => expect(screen.getByText("Ready")).toBeInTheDocument());
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Clean cache" }),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("button", { name: "Clean logs" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Clean diagnostics" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Clean models" }),
    ).not.toBeInTheDocument();
  });
});
