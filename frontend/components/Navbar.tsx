import Button from "./Button";

interface NavbarProps {
  onLogout?: () => void;
}

export default function Navbar({ onLogout }: NavbarProps) {
  return (
    <nav className="flex h-16 items-center justify-between border-b border-border bg-white px-6">
      <span className="text-lg font-semibold text-primary-700">WritOauth</span>
      {onLogout && (
        <Button variant="secondary" onClick={onLogout}>
          Log out
        </Button>
      )}
    </nav>
  );
}
