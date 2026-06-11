import { createRootRoute, createRoute } from "@tanstack/react-router";
import type { ReactNode } from "react";

export type ConsoleSection = "voices" | "playground" | "health" | "developer";

export const consoleSections = [
  { id: "voices", label: "Voices", hash: "#voices" },
  { id: "playground", label: "Playground", hash: "#playground" },
  { id: "health", label: "Health", hash: "#health" },
  { id: "developer", label: "Developer", hash: "#developer" },
] as const satisfies ReadonlyArray<{
  id: ConsoleSection;
  label: string;
  hash: `#${ConsoleSection}`;
}>;

export function createConsoleRouteTree(AppComponent: () => ReactNode) {
  const rootRoute = createRootRoute({ component: AppComponent });
  const sectionRoutes = consoleSections.map((section) =>
    createRoute({
      getParentRoute: () => rootRoute,
      path: section.id,
      component: AppComponent,
    }),
  );
  return rootRoute.addChildren(sectionRoutes);
}
