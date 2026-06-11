import { AppShell } from "@features/app-shell/AppShell";
import { createConsoleRouteTree } from "@features/app-shell/routes";
import { MeryQueryProvider } from "@shared/query/QueryProvider";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const router = createRouter({ routeTree: createConsoleRouteTree(AppShell) });

const root = document.querySelector("#root");

if (!root) {
  throw new Error("Mery Console root element is missing");
}

createRoot(root).render(
  <StrictMode>
    <MeryQueryProvider>
      <RouterProvider router={router} />
    </MeryQueryProvider>
  </StrictMode>,
);
