"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export default function Home() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-zinc-400 text-sm">Loading...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-4 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          RowApp
        </h1>
        <p className="mt-4 max-w-md text-lg text-zinc-500">
          Track your rowing workouts, monitor progress, and compete with your
          team.
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <Link
            href="/login"
            className="rounded-lg bg-zinc-900 px-6 py-2.5 text-sm font-semibold text-white hover:bg-zinc-800 transition-colors"
          >
            Login
          </Link>
          <Link
            href="/register"
            className="rounded-lg border border-zinc-300 px-6 py-2.5 text-sm font-semibold text-zinc-900 hover:bg-zinc-100 transition-colors"
          >
            Sign Up
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 text-center">
      <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
        Welcome back, {user.display_name}
      </h1>

      <div className="mt-10 grid w-full max-w-xs grid-cols-1 gap-6">
        <div className="rounded-xl border border-zinc-200 bg-white p-6">
          <p className="text-3xl font-bold">0</p>
          <p className="mt-1 text-sm text-zinc-500">Total Workouts</p>
        </div>
      </div>

      <a
        href="/workouts/new"
        className="mt-8 rounded-lg bg-zinc-900 px-6 py-2.5 text-sm font-semibold text-white hover:bg-zinc-800 transition-colors"
      >
        Log Workout
      </a>
    </div>
  );
}
