import * as Tabs from "@radix-ui/react-tabs";
import { useEffect, useState } from "react";
import { type ConsoleSection, consoleSections } from "./routes";

function sectionFromHash(hash: string): ConsoleSection {
  const match = consoleSections.find((section) => section.hash === hash);
  return match?.id ?? "voices";
}

interface SectionTabsProps {
  panels: Record<ConsoleSection, React.ReactNode>;
}

export function SectionTabs({ panels }: SectionTabsProps) {
  const [activeSection, setActiveSection] = useState<ConsoleSection>(() =>
    sectionFromHash(globalThis.location?.hash ?? "#voices"),
  );
  const [visited, setVisited] = useState<ReadonlySet<ConsoleSection>>(
    () => new Set([sectionFromHash(globalThis.location?.hash ?? "#voices")]),
  );

  useEffect(() => {
    const syncFromHash = () => {
      const section = sectionFromHash(globalThis.location.hash);
      setActiveSection(section);
      setVisited((prev) =>
        prev.has(section) ? prev : new Set([...prev, section]),
      );
    };
    syncFromHash();
    globalThis.addEventListener("hashchange", syncFromHash);
    return () => globalThis.removeEventListener("hashchange", syncFromHash);
  }, []);

  return (
    <Tabs.Root
      value={activeSection}
      onValueChange={(value) => {
        const section = value as ConsoleSection;
        setActiveSection(section);
        setVisited((prev) =>
          prev.has(section) ? prev : new Set([...prev, section]),
        );
      }}
    >
      <nav aria-label="User Mode navigation">
        <Tabs.List aria-label="Console sections" className="tabs-list">
          {consoleSections.map((section) => (
            <Tabs.Trigger asChild key={section.id} value={section.id}>
              <a className="tab-trigger" href={section.hash}>
                {section.label}
              </a>
            </Tabs.Trigger>
          ))}
        </Tabs.List>
      </nav>
      {consoleSections.map((section) =>
        visited.has(section.id) ? (
          <Tabs.Content
            forceMount
            hidden={activeSection !== section.id}
            key={section.id}
            value={section.id}
          >
            {panels[section.id]}
          </Tabs.Content>
        ) : null,
      )}
    </Tabs.Root>
  );
}
