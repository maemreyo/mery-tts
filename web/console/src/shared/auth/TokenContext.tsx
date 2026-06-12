import { createContext, useContext } from "react";

const TokenContext = createContext<string>("");

export const TokenProvider = TokenContext.Provider;

export function useToken(): string {
  return useContext(TokenContext);
}
