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
              voice_id: "piper-plus.fr-fr.demo",
              display_name: "French Demo",
              engine_id: "piper-plus",
              supported_locales: ["fr-FR"],
              risk_class: "stock",
              consent_required: false,
              consent_status: "not_required",
            },
          ],
        }),
      ),
      // No installed voices — French Demo is not installed
      http.get("/v1/voices/installed", () =>
        HttpResponse.json({ schema_version: "v1", voices: [] }),
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

  it("renders text input textarea", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(screen.getByLabelText("Voice")).toBeInTheDocument(),
    );

    expect(
      screen.getByRole("textbox", { name: "Text to synthesize" }),
    ).toBeInTheDocument();
  });

  it("auto-selects the first installed voice so Synthesize fires immediately", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    // Wait for the voice picker to appear with the auto-selected voice
    await waitFor(() =>
      expect(
        screen.getByRole("combobox", { name: "Voice" }),
      ).toBeInTheDocument(),
    );

    // Auto-select means clicking Synthesize immediately should NOT show a validation error
    await userEvent.click(screen.getByRole("button", { name: /Synthesize/ }));

    await waitFor(() =>
      expect(
        screen.queryByText("Choose a voice before synthesizing."),
      ).not.toBeInTheDocument(),
    );
  });

  it("synthesizes speech using the selected installed voice", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("option", { name: "Demo (en-US)" }),
      ).toBeInTheDocument(),
    );

    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Voice" }),
      "piper-plus.en-us.demo",
    );

    await userEvent.click(screen.getByRole("button", { name: /Synthesize/ }));

    await waitFor(() =>
      expect(screen.getByRole("heading", { level: 2 })).toBeInTheDocument(),
    );
    // On success the audio element is rendered
    await waitFor(() => expect(document.querySelector("audio")).not.toBeNull());
  });

  it("smoke is recorded via onSuccess when synthesis succeeds", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("option", { name: "Demo (en-US)" }),
      ).toBeInTheDocument(),
    );

    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Voice" }),
      "piper-plus.en-us.demo",
    );

    await userEvent.click(screen.getByRole("button", { name: /Synthesize/ }));

    // No error message means onSuccess path was taken
    await waitFor(() =>
      expect(screen.queryByText(/Synthesis failed/)).not.toBeInTheDocument(),
    );
  });

  it("smoke is recorded via onError when backend returns error", async () => {
    server.use(
      http.post(
        "/v1/audio/speech",
        () => new HttpResponse(null, { status: 500 }),
      ),
    );

    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("option", { name: "Demo (en-US)" }),
      ).toBeInTheDocument(),
    );

    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Voice" }),
      "piper-plus.en-us.demo",
    );
    await userEvent.click(screen.getByRole("button", { name: /Synthesize/ }));

    // onError path: error message is shown
    await waitFor(() =>
      expect(screen.getByText(/Synthesis failed/)).toBeInTheDocument(),
    );
  });

  it("advanced options toggle expands and collapses override model ID field", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Advanced" }),
      ).toBeInTheDocument(),
    );

    const toggle = screen.getByRole("button", { name: "Advanced" });
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
        screen.getByRole("button", { name: "Advanced" }),
      ).toBeInTheDocument(),
    );

    await userEvent.click(screen.getByRole("button", { name: "Advanced" }));

    await userEvent.type(
      screen.getByLabelText("Override model ID"),
      "pack.en-us-libritts-high",
    );

    await userEvent.click(screen.getByRole("button", { name: /Synthesize/ }));

    await waitFor(() => expect(document.querySelector("audio")).not.toBeNull());
  });

  it("advanced override empty falls back to picker voice — no validation error", async () => {
    // When Advanced is open but override is empty, activeModelId = selectedVoiceId
    // (auto-selected), so Synthesize should fire without a validation error.
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Advanced" }),
      ).toBeInTheDocument(),
    );

    await userEvent.click(screen.getByRole("button", { name: "Advanced" }));
    // Override input is empty — fall through to selected voice
    await userEvent.click(screen.getByRole("button", { name: /Synthesize/ }));

    await waitFor(() =>
      expect(
        screen.queryByText(
          "Enter an override model ID or select a voice above.",
        ),
      ).not.toBeInTheDocument(),
    );
  });

  it("shows synthesis error when backend returns error", async () => {
    server.use(
      http.post(
        "/v1/audio/speech",
        () => new HttpResponse(null, { status: 500 }),
      ),
    );

    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("option", { name: "Demo (en-US)" }),
      ).toBeInTheDocument(),
    );

    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Voice" }),
      "piper-plus.en-us.demo",
    );
    await userEvent.click(screen.getByRole("button", { name: /Synthesize/ }));

    await waitFor(() =>
      expect(screen.getByText(/Synthesis failed/)).toBeInTheDocument(),
    );
  });

  it("Word timings toggle renders when voices are available", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(screen.getByLabelText("Voice")).toBeInTheDocument(),
    );

    expect(
      screen.getByRole("switch", { name: "Word timings" }),
    ).toBeInTheDocument();
  });

  it("audio element is rendered after successful synthesis", async () => {
    renderWithProviders(<PlaygroundPanel token="test-token" />);

    await waitFor(() =>
      expect(
        screen.getByRole("option", { name: "Demo (en-US)" }),
      ).toBeInTheDocument(),
    );

    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Voice" }),
      "piper-plus.en-us.demo",
    );
    await userEvent.click(screen.getByRole("button", { name: /Synthesize/ }));

    await waitFor(() => expect(document.querySelector("audio")).not.toBeNull());
  });
});
