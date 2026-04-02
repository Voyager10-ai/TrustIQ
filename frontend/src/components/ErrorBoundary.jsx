import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError() {
        // Update state so the next render will show the fallback UI.
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        // You can also log the error to an error reporting service
        console.error("ErrorBoundary caught an error", error, errorInfo);
        this.setState({
            error: error,
            errorInfo: errorInfo
        });
    }

    render() {
        if (this.state.hasError) {
            // You can render any custom fallback UI
            return (
                <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center p-6 text-slate-200 font-sans">
                    <div className="bg-[#111827] border border-red-500/20 rounded-2xl p-8 max-w-xl w-full shadow-2xl text-center">
                        <div className="w-16 h-16 bg-red-500/10 border border-red-500/20 rounded-full flex items-center justify-center text-3xl mx-auto mb-6">⚠️</div>
                        <h1 className="text-2xl font-bold text-white mb-4">Something went wrong</h1>
                        <p className="text-slate-400 mb-8">
                            An unexpected error occurred in the application. Please try refreshing the page or contact support if the issue persists.
                        </p>
                        <div className="bg-black/30 p-4 rounded-lg text-left overflow-x-auto text-xs font-mono text-red-400 mb-8 border border-white/5">
                            {this.state.error && this.state.error.toString()}
                            <br />
                            {this.state.errorInfo && this.state.errorInfo.componentStack}
                        </div>
                        <button
                            onClick={() => window.location.reload()}
                            className="bg-red-600 hover:bg-red-700 text-white font-medium py-2.5 px-8 rounded-lg transition-colors border border-red-500 shadow-lg shadow-red-500/20"
                        >
                            Refresh Page
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
