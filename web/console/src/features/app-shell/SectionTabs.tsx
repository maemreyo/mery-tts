import * as Tabs from "@radix-ui/react-tabs";
import { Link } from "@tanstack/react-router";
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

  useEffect(() => {
    const syncFromHash = () =>
      setActiveSection(sectionFromHash(globalThis.location.hash));
    syncFromHash();
    globalThis.addEventListener("hashchange", syncFromHash);
    return () => globalThis.removeEventListener("hashchange", syncFromHash);
  }, []);

  return (
    <Tabs.Root
      value={activeSection}
      onValueChange={(value) => setActiveSection(value as ConsoleSection)}
    >
      <nav aria-label="User Mode navigation">
        <Tabs.List aria-label="Console sections" className="tabs-list">
          {consoleSections.map((section) => (
            <Tabs.Trigger asChild key={section.id} value={section.id}>
              <Link hash={section.id} to="/" className="tab-trigger">
                {section.label}
              </Link>
            </Tabs.Trigger>
          ))}
        </Tabs.List>
      </nav>
      {consoleSections.map((section) => (
        <Tabs.Content
          forceMount
          hidden={activeSection !== section.id}
          key={section.id}
          value={section.id}
        >
          {panels[section.id]}
        </Tabs.Content>
      ))}
    </Tabs.Root>
  );
}
