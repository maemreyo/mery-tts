export type ConsoleSection =
  | "overview"
  | "voices"
  | "playground"
  | "health"
  | "developer";

export const consoleSections = [
  { id: "overview", label: "Overview", hash: "#overview" },
  { id: "voices", label: "Voices", hash: "#voices" },
  { id: "playground", label: "Playground", hash: "#playground" },
  { id: "health", label: "Health", hash: "#health" },
  { id: "developer", label: "Developer", hash: "#developer" },
] as const satisfies ReadonlyArray<{
  id: ConsoleSection;
  label: string;
  hash: `#${ConsoleSection}`;
}>;
