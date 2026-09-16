import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error caught by ErrorBoundary:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="max-w-xl mx-auto my-12 p-8 bg-[#FFFDF9] border-4 border-black shadow-[8px_8px_0px_0px_#000] text-center space-y-4 font-['Plus_Jakarta_Sans']">
          <div className="inline-block p-4 bg-[#FB7185] border-3 border-black shadow-[4px_4px_0px_0px_#000]">
            <AlertTriangle className="w-10 h-10 text-black stroke-[2.5]" />
          </div>

          <h2 className="text-2xl font-black uppercase font-['Space_Grotesk'] tracking-tight">
            SOMETHING WENT WRONG
          </h2>

          <p className="font-mono text-xs text-gray-700 bg-[#FAF7F2] border-2 border-black p-3 text-left overflow-auto max-h-32">
            {this.state.error?.message || 'An unexpected rendering error occurred.'}
          </p>

          <p className="text-xs text-gray-600 font-bold">
            Your data and tax computations in the database are completely safe.
          </p>

          <button
            onClick={this.handleReset}
            className="inline-flex items-center gap-2 bg-[#FACC15] hover:bg-yellow-400 text-black px-6 py-2.5 border-3 border-black font-black font-mono text-sm shadow-[4px_4px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all uppercase"
          >
            <RefreshCw className="w-4 h-4" />
            <span>RELOAD PAGE</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
