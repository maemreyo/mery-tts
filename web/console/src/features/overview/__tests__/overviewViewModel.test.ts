import type { HealthResponse } from "@shared/api/meryApi";
import type { VoiceViewModel } from "@shared/api/voiceViewModels";
import { describe, expect, it } from "vitest";
import { deriveOverviewViewModel } from "../overviewViewModel";

const baseVoice: VoiceViewModel = {
  id: "v1",
  modelId: "model-1",
  title: "Voice 1",
  engine: "vits",
  locales: "en-US",
  installed: true,
  installedLabel: "installed",
  governanceLabel: "allowed (low)",
  governanceStatus: "allowed",
  installable: false,
};

const readyHealth: HealthResponse = {
  schema_version: "v1",
  health_status: "healthy",
  ready: true,
  total_usable_voices: 1,
};

const notReadyHealth: HealthResponse = {
  schema_version: "v1",
  health_status: "degraded",
  ready: false,
  total_usable_voices: 0,
};

const defaults = {
  health: readyHealth,
  healthError: false,
  voices: [baseVoice],
  isHealthLoading: false,
  isVoicesLoading: false,
};

describe("deriveOverviewViewModel", () => {
  describe("disconnected", () => {
    it("headline includes 'Connect'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "disconnected",
        health: null,
        voices: null,
      });
      expect(vm.headline).toContain("Connect");
    });

    it("primary action target is 'connect'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "disconnected",
        health: null,
        voices: null,
      });
      expect(vm.primaryAction.target).toBe("connect");
    });

    it("connection status tile level is 'error'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "disconnected",
        health: null,
        voices: null,
      });
      const tile = vm.statusTiles.find((t) => t.label === "Connection");
      expect(tile?.level).toBe("error");
    });
  });

  describe("checking (connectionStatus === 'checking')", () => {
    it("headline includes 'Connecting'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "checking",
        health: null,
      });
      expect(vm.headline).toContain("Connecting");
    });

    it("connection status tile level is 'neutral'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "checking",
        health: null,
      });
      const tile = vm.statusTiles.find((t) => t.label === "Connection");
      expect(tile?.level).toBe("neutral");
      expect(tile?.value).toBe("Checking…");
    });
  });

  describe("connected + healthError", () => {
    it("headline includes 'Cannot reach'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: null,
        healthError: true,
      });
      expect(vm.headline).toContain("Cannot reach");
    });

    it("primary action target is 'health'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: null,
        healthError: true,
      });
      expect(vm.primaryAction.target).toBe("health");
    });

    it("server status tile level is 'error'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: null,
        healthError: true,
      });
      const tile = vm.statusTiles.find((t) => t.label === "Server");
      expect(tile?.level).toBe("error");
    });
  });

  describe("connected + health not ready", () => {
    it("headline includes 'not ready'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: notReadyHealth,
        healthError: false,
      });
      expect(vm.headline).toContain("not ready");
    });

    it("secondary actions include 'Developer Mode'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: notReadyHealth,
        healthError: false,
      });
      expect(
        vm.secondaryActions.some((a) => a.label === "Developer Mode"),
      ).toBe(true);
    });
  });

  describe("connected + ready + no voices", () => {
    it("headline includes 'No voices'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: readyHealth,
        healthError: false,
        voices: [],
      });
      expect(vm.headline).toContain("No voices");
    });

    it("primary action target is 'voices'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: readyHealth,
        healthError: false,
        voices: [],
      });
      expect(vm.primaryAction.target).toBe("voices");
    });

    it("voices tile level is 'warn'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: readyHealth,
        healthError: false,
        voices: [],
      });
      const tile = vm.statusTiles.find((t) => t.label === "Voices");
      expect(tile?.level).toBe("warn");
      expect(tile?.value).toBe("None installed");
    });
  });

  describe("connected + ready + voices available", () => {
    it("headline includes 'ready'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: readyHealth,
        healthError: false,
        voices: [baseVoice],
      });
      expect(vm.headline).toContain("ready");
    });

    it("primary action target is 'playground'", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: readyHealth,
        healthError: false,
        voices: [baseVoice],
      });
      expect(vm.primaryAction.target).toBe("playground");
    });

    it("secondary actions include Browse Voices and View Health", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: readyHealth,
        healthError: false,
        voices: [baseVoice],
      });
      const targets = vm.secondaryActions.map((a) => a.target);
      expect(targets).toContain("voices");
      expect(targets).toContain("health");
    });

    it("voices tile shows count and 'ok' level", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: readyHealth,
        healthError: false,
        voices: [baseVoice, { ...baseVoice, id: "v2", modelId: "model-2" }],
      });
      const tile = vm.statusTiles.find((t) => t.label === "Voices");
      expect(tile?.level).toBe("ok");
      expect(tile?.value).toBe("2 available");
    });
  });

  describe("status tiles", () => {
    it("always returns exactly 3 tiles", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: readyHealth,
        voices: [baseVoice],
      });
      expect(vm.statusTiles).toHaveLength(3);
    });

    it("shows 'Loading…' for voices tile when isVoicesLoading is true", () => {
      const vm = deriveOverviewViewModel({
        ...defaults,
        connectionStatus: "connected",
        health: readyHealth,
        voices: null,
        isVoicesLoading: true,
      });
      const tile = vm.statusTiles.find((t) => t.label === "Voices");
      expect(tile?.value).toBe("Loading…");
    });
  });
});
