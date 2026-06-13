import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  sectionName: string;
  onGoToOverview: () => void;
}

interface State {
  hasError: boolean;
}

export class PanelErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div role="alert" style={{ padding: 24 }}>
          <p>Something went wrong in {this.props.sectionName}.</p>
          <button type="button" onClick={this.props.onGoToOverview}>
            Go to Overview
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
