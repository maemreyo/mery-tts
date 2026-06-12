import { consoleSections, type ConsoleSection } from "./routes";
import { useNavigation } from "./NavigationContext";

interface ContentAreaProps {
  panels: Record<ConsoleSection, React.ReactNode>;
}

export function ContentArea({ panels }: ContentAreaProps) {
  const { activeSection, visited } = useNavigation();

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
            {panels[section.id]}
          </div>
        );
      })}
    </>
  );
}
