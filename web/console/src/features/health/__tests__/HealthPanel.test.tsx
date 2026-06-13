import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
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
});
