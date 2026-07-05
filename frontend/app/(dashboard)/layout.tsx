export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <aside className="w-64 bg-gray-800 text-white p-4">
        <p>Sidebar placeholder</p>
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
