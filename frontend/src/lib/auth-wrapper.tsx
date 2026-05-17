"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { AuthProvider, useAuth } from "@/lib/auth-context";

function NavBar() {
  const { user, loading, logout } = useAuth();

  return (
    <header className="border-b border-zinc-200 bg-white">
      <nav className="mx-auto flex h-14 max-w-4xl items-center justify-between px-4">
        <Link href="/" className="text-lg font-bold tracking-tight">
          RowApp
        </Link>

        <div className="flex items-center gap-4">
          {loading ? null : user ? (
            <>
              <span className="text-sm text-zinc-500 hidden sm:inline">
                {user.display_name}
              </span>
              <button
                onClick={logout}
                className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors"
              >
                Login
              </Link>
              <Link
                href="/register"
                className="rounded-lg bg-zinc-900 px-3 py-1.5 text-sm font-semibold text-white hover:bg-zinc-800 transition-colors"
              >
                Sign Up
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}

export function AuthWrapper({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <NavBar />
      <main className="flex flex-1 flex-col">{children}</main>
    </AuthProvider>
  );
}
