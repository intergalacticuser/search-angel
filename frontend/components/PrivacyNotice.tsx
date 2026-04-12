export default function PrivacyNotice() {
  return (
    <footer className="text-center py-6 text-xs text-angel-muted/50">
      <div className="flex items-center justify-center gap-4">
        <span>No cookies</span>
        <span className="w-1 h-1 rounded-full bg-angel-muted/30" />
        <span>No tracking</span>
        <span className="w-1 h-1 rounded-full bg-angel-muted/30" />
        <span>No profiling</span>
        <span className="w-1 h-1 rounded-full bg-angel-muted/30" />
        <span>Stateless queries</span>
      </div>
      <p className="mt-2">Search Angel v0.1.0</p>
    </footer>
  );
}
