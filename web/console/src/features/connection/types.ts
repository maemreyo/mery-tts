export type ConnectionStatus = "connected" | "checking" | "disconnected";

export interface SessionValues {
  token: string;
  remember: boolean;
}
