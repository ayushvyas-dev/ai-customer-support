"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, loading } = useAuth();

  React.useEffect(() => {
    if (!loading) {
      if (isAuthenticated) {
        router.replace("/events");
      } else {
        router.replace("/login");
      }
    }
  }, [isAuthenticated, loading, router]);

  return (
    <div className="flex h-[70vh] items-center justify-center">
      <div className="h-5 w-5 animate-spin rounded-full border-2 border-[#111111] border-t-transparent" />
    </div>
  );
}
