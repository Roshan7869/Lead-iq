"use client";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="glass-panel p-8 text-center max-w-md w-full">
        <h2 className="text-2xl font-bold text-destructive mb-2">Something went wrong</h2>
        <p className="text-muted-foreground mb-6 text-sm">
          An unexpected error occurred. Please try again or refresh the page.
        </p>
        <button
          onClick={reset}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90 transition-opacity"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
