import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('TalentRank UI Error Caught by Boundary:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-cream-100 flex items-center justify-center p-6 text-center">
          <div className="bg-white rounded-2xl border border-sage-muted p-8 max-w-md shadow-xs">
            <div className="w-12 h-12 rounded-2xl bg-terracotta-light text-terracotta-dark mx-auto flex items-center justify-center mb-4 border border-terracotta/40">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-charcoal">Something went wrong</h2>
            <p className="text-xs text-charcoal-muted mt-2 mb-6 leading-relaxed">
              An unexpected UI error occurred: {this.state.error?.message || 'Unknown error'}. You can refresh the dashboard safely.
            </p>
            <button
              onClick={this.handleReload}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-olive text-white text-xs font-semibold hover:bg-olive-dark transition shadow-xs cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reload Workspace</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
