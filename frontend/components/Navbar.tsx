import Link from "next/link";

import Button from "./Button";
import ThemeToggle from "./ThemeToggle";

interface NavbarProps {
  onLogout?: () => void;
}

export default function Navbar({ onLogout }: NavbarProps) {
  return (
    <nav className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-bg-elevated/80 px-4 backdrop-blur-xl sm:px-6">
      <Link
        href="/dashboard"
        className="rounded-md text-title3 font-semibold tracking-tight text-text"
      >
        Writ<span className="text-primary-600">Oauth</span>
      </Link>
      <div className="flex items-center gap-3">
        <ThemeToggle />
        {onLogout && (
          <Button variant="secondary" onClick={onLogout}>
            Log out
          </Button>
        )}
      </div>
    </nav>
  );
}
