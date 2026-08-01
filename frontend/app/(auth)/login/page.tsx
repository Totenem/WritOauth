import { LoginForm } from "@/features/authentication";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-bg-subtle px-4">
      <div className="w-full max-w-sm">
        <h1 className="mb-6 text-center text-2xl font-bold text-primary-700">
          WritOauth
        </h1>
        <LoginForm />
      </div>
    </main>
  );
}
