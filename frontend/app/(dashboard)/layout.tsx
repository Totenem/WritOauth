"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { AppHeader, Spinner } from "@/components";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { teacher, isAuthenticated, isLoading, logout } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  const handleLogout = async () => {
    await logout();
    router.replace("/login");
  };

  // Only the auth check blocks the whole page - once the token is known to
  // be good the shell renders immediately and each page skeletons its own
  // content. Previously this spinner covered the entire viewport on every
  // dashboard navigation.
  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-bg">
      <AppHeader teacher={teacher} onLogout={handleLogout} />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">{children}</main>
      <footer className="border-t border-border py-5 text-center text-caption text-text-subtle">
        &copy; {new Date().getFullYear()} WritOath Educator Platform. Protecting human authorial
        identity in academia.
      </footer>
    </div>
  );
}
