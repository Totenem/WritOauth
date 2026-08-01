export default function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-white p-4 shadow-sm">
      {children}
    </div>
  );
}
