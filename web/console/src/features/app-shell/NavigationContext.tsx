import { createContext, useContext, useEffect, useState } from "react";
import { type ConsoleSection, consoleSections } from "./routes";

export interface NavigationState {
  activeSection: ConsoleSection;
  visited: ReadonlySet<ConsoleSection>;
  navigate: (section: ConsoleSection) => void;
}

function sectionFromHash(hash: string): ConsoleSection {
  const match = consoleSections.find((s) => s.hash === hash);
  return match?.id ?? "overview";
}

function withVisited(
  prev: ReadonlySet<ConsoleSection>,
  section: ConsoleSection,
): ReadonlySet<ConsoleSection> {
  return prev.has(section) ? prev : new Set([...prev, section]);
}

const NavigationContext = createContext<NavigationState | null>(null);

export function NavigationProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const initial = sectionFromHash(globalThis.location?.hash ?? "");

  const [activeSection, setActiveSection] = useState<ConsoleSection>(initial);
  const [visited, setVisited] = useState<ReadonlySet<ConsoleSection>>(
    () => new Set([initial]),
  );

  useEffect(() => {
    const sync = () => {
      const section = sectionFromHash(globalThis.location.hash);
      setActiveSection(section);
      setVisited((prev) => withVisited(prev, section));
    };
    sync();
    globalThis.addEventListener("hashchange", sync);
    return () => globalThis.removeEventListener("hashchange", sync);
  }, []);

  function navigate(section: ConsoleSection) {
    globalThis.location.hash = `#${section}`;
  }

  return (
    <NavigationContext.Provider value={{ activeSection, visited, navigate }}>
      {children}
    </NavigationContext.Provider>
  );
}

export function useNavigation(): NavigationState {
  const ctx = useContext(NavigationContext);
  if (!ctx)
    throw new Error("useNavigation must be used within NavigationProvider");
  return ctx;
}
