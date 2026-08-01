export default function Spinner() {
  return (
    <div
      role="status"
      aria-label="Loading"
      className="h-6 w-6 animate-spin rounded-full border-2 border-primary-200 border-t-primary-600"
    />
  );
}
