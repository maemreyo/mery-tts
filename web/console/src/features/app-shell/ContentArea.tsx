import { useNavigation } from "./NavigationContext";
import { PanelErrorBoundary } from "./PanelErrorBoundary";
import { type ConsoleSection, consoleSections } from "./routes";

interface ContentAreaProps {
  panels: Record<ConsoleSection, React.ReactNode>;
}

export function ContentArea({ panels }: ContentAreaProps) {
  const { activeSection, visited, navigate } = useNavigation();

  return (
    <>
      {consoleSections.map((section) => {
        if (!visited.has(section.id)) return null;
        return (
          <div
            key={section.id}
            hidden={activeSection !== section.id}
            className="page-section"
          >
            <PanelErrorBoundary
              key={`${section.id}-eb`}
              sectionName={section.label}
              onGoToOverview={() => navigate("overview")}
            >
              {panels[section.id]}
            </PanelErrorBoundary>
          </div>
        );
      })}
    </>
  );
}
