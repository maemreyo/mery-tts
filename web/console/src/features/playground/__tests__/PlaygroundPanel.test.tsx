import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { server } from "../../../test/handlers";
import { renderWithProviders } from "../../../test/renderWithProviders";
import { PlaygroundPanel } from "../PlaygroundPanel";

describe("PlaygroundPanel", () => {
  it("shows enter token prompt when no token is provided", () => {
    renderWithProviders(<PlaygroundPanel token="" />);
    expect(
      screen.getByText("Enter a bearer token to use the Playground."),
    ).toBeInTheDocument();
  });

  it("shows install voice link when no voices are installed", async () => {
    server.use(
      http.get("/v1/catalog/voices", () =>
        HttpResponse.json({
          schema_version: "v1",
          voices: [
            {
              id: "voice.fr-fr",
              model_id: "pack.fr-fr",
              name: "French Demo",
              engine: "piper-plus",
              supported_locales: ["fr-FR"],
              installed: false,
              risk_class: "stock",
              governance_status: "allowed",
            },
          ],
        }),
      ),
    );

    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByText("No installed voices found."),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("button", { name: "Install a voice →" }),
    ).toBeInTheDocument();
  });

  it("renders voice picker with installed voices", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(screen.getByLabelText("Voice")).toBeInTheDocument(),
    );
  });

  it("shows validation error when submitting without selecting a voice", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Run speech smoke" }),
      ).toBeInTheDocument(),
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Run speech smoke" }),
    );

    await waitFor(() =>
      expect(
        screen.getByText("Choose a voice before running smoke."),
      ).toBeInTheDocument(),
    );
  });

  it("runs speech smoke using the selected installed voice", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("option", { name: "English Demo" }),
      ).toBeInTheDocument(),
    );

    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Voice" }),
      "pack.en-us",
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Run speech smoke" }),
    );

    await waitFor(() =>
      expect(screen.getByText("Speech smoke succeeded.")).toBeInTheDocument(),
    );
  });

  it("advanced options toggle expands and collapses override model ID field", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Advanced options" }),
      ).toBeInTheDocument(),
    );

    const toggle = screen.getByRole("button", { name: "Advanced options" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(
      screen.queryByLabelText("Override model ID"),
    ).not.toBeInTheDocument();

    await userEvent.click(toggle);

    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByLabelText("Override model ID")).toBeInTheDocument();
    expect(
      screen.getByText("Overrides the selected voice above"),
    ).toBeInTheDocument();

    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(
      screen.queryByLabelText("Override model ID"),
    ).not.toBeInTheDocument();
  });

  it("uses raw override model ID when advanced options are expanded and filled", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Advanced options" }),
      ).toBeInTheDocument(),
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Advanced options" }),
    );

    await userEvent.type(
      screen.getByLabelText("Override model ID"),
      "pack.en-us-libritts-high",
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Run speech smoke" }),
    );

    await waitFor(() =>
      expect(screen.getByText("Speech smoke succeeded.")).toBeInTheDocument(),
    );
  });

  it("shows validation error when advanced override is empty and no voice selected", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Advanced options" }),
      ).toBeInTheDocument(),
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Advanced options" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Run speech smoke" }),
    );

    await waitFor(() =>
      expect(
        screen.getByText("Enter an override model ID or select a voice above."),
      ).toBeInTheDocument(),
    );
  });

  it("output has role=status and reflects pending/success/failure states", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("option", { name: "English Demo" }),
      ).toBeInTheDocument(),
    );

    expect(screen.getByRole("status")).toHaveTextContent(
      "Ready for backend speech smoke.",
    );

    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Voice" }),
      "pack.en-us",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Run speech smoke" }),
    );

    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(
        "Speech smoke succeeded.",
      ),
    );
  });

  it("shows speech smoke failed when backend returns error", async () => {
    server.use(
      http.post(
        "/v1/audio/speech",
        () => new HttpResponse(null, { status: 500 }),
      ),
    );

    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("option", { name: "English Demo" }),
      ).toBeInTheDocument(),
    );

    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Voice" }),
      "pack.en-us",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Run speech smoke" }),
    );

    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(
        "Speech smoke failed with backend error.",
      ),
    );
  });

  it("Show word timings toggle renders when voices are available", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(screen.getByLabelText("Voice")).toBeInTheDocument(),
    );

    expect(
      screen.getByRole("switch", { name: "Show word timings" }),
    ).toBeInTheDocument();
  });

  it("Result output shows Speech smoke succeeded in normal mode", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("option", { name: "English Demo" }),
      ).toBeInTheDocument(),
    );

    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Voice" }),
      "pack.en-us",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Run speech smoke" }),
    );

    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(
        "Speech smoke succeeded.",
      ),
    );
  });
});
