import { AppShell } from "@features/app-shell/AppShell";
import { MeryQueryProvider } from "@shared/query/QueryProvider";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const root = document.querySelector("#root");

if (!root) {
  throw new Error("Mery Console root element is missing");
}

createRoot(root).render(
  <StrictMode>
    <MeryQueryProvider>
      <AppShell />
    </MeryQueryProvider>
  </StrictMode>,
);
