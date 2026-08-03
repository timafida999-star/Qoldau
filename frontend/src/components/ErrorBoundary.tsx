import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RotateCw } from "lucide-react";

import i18n from "@/i18n";
import { Button } from "@/components/ui/button";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

/**
 * Last line of defence: any render error used to blank the whole page
 * (an empty #root with no way back). Class component because React only
 * exposes error boundaries through the class lifecycle. i18n is used
 * directly since hooks are unavailable here.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unhandled render error:", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="container flex min-h-[60vh] max-w-lg flex-col items-center justify-center py-20 text-center">
          <AlertTriangle className="mb-4 h-12 w-12 text-destructive" />
          <h1 className="text-2xl font-semibold">{i18n.t("errors.crashTitle")}</h1>
          <p className="mt-2 text-muted-foreground">{i18n.t("errors.crashBody")}</p>
          <Button className="mt-6" onClick={() => window.location.reload()}>
            <RotateCw className="mr-2 h-4 w-4" />
            {i18n.t("errors.crashReload")}
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}
