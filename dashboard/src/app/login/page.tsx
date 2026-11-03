"use client";

import * as React from "react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ShieldCheck, Lock, User, AlertCircle, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = React.useState("admin");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(username, password);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to sign in. Check your credentials.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center bg-neutral-50/50 p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-black text-white shadow-xs">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-neutral-900">
            Customer Support Automation
          </h1>
          <p className="text-xs text-neutral-500 mt-1">
            Admin console for AI email triage, tickets, and knowledge base
          </p>
        </div>

        <Card className="border-neutral-200 shadow-sm bg-white">
          <form onSubmit={handleSubmit}>
            <CardHeader className="space-y-1 pb-4">
              <CardTitle className="text-base font-semibold">Dashboard Login</CardTitle>
              <CardDescription className="text-xs">
                Enter your credentials to access the support admin center.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              {error && (
                <div className="flex items-center space-x-2 rounded-md border border-neutral-300 bg-neutral-100 p-3 text-xs text-neutral-900">
                  <AlertCircle className="h-4 w-4 shrink-0 text-neutral-800" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-1.5">
                <label
                  htmlFor="username"
                  className="text-xs font-medium text-neutral-700 flex items-center space-x-1"
                >
                  <User className="h-3 w-3" />
                  <span>Username</span>
                </label>
                <Input
                  id="username"
                  type="text"
                  placeholder="admin"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoComplete="username"
                  className="h-9"
                />
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="password"
                  className="text-xs font-medium text-neutral-700 flex items-center space-x-1"
                >
                  <Lock className="h-3 w-3" />
                  <span>Password</span>
                </label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  className="h-9"
                />
                <p className="text-[11px] text-neutral-400">
                  Configured via DASHBOARD_USERNAME and DASHBOARD_PASSWORD in .env
                </p>
              </div>
            </CardContent>

            <CardFooter className="pt-2">
              <Button
                type="submit"
                className="w-full bg-black text-white hover:bg-neutral-800 h-9 text-xs font-semibold"
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center space-x-2">
                    <span className="h-3 w-3 animate-spin rounded-full border border-white border-t-transparent" />
                    <span>Signing in...</span>
                  </span>
                ) : (
                  <span className="flex items-center justify-center space-x-1">
                    <span>Sign In</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </span>
                )}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}

