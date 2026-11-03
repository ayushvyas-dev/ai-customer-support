"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  Activity,
  Ticket,
  BookOpen,
  LogOut,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();
  const { user, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated && pathname === "/login") {
    return null;
  }

  const navItems = [
    {
      label: "Events",
      href: "/events",
      icon: Activity,
    },
    {
      label: "Tickets",
      href: "/tickets",
      icon: Ticket,
    },
    {
      label: "Knowledge Base",
      href: "/knowledge-base",
      icon: BookOpen,
    },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-neutral-200 bg-white/95 backdrop-blur-xs">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center space-x-6">
          <Link href="/events" className="flex items-center space-x-2 font-bold tracking-tight text-black text-sm">
            <span className="flex h-6 w-6 items-center justify-center rounded-sm bg-black text-white text-xs font-black">
              AI
            </span>
            <span>CUSTOMER SUPPORT</span>
          </Link>

          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center space-x-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                    isActive
                      ? "bg-black text-white"
                      : "text-neutral-600 hover:bg-neutral-100 hover:text-black"
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs text-neutral-500 border border-neutral-200 rounded-md px-2 py-1 bg-neutral-50">
            <ShieldCheck className="h-3.5 w-3.5 text-black" />
            <span className="font-mono">{user || "admin"}</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            className="text-xs text-neutral-600 hover:text-black hover:bg-neutral-100 h-8 px-2.5"
          >
            <LogOut className="mr-1.5 h-3.5 w-3.5" />
            Logout
          </Button>
        </div>
      </div>

      {/* Mobile nav */}
      <div className="flex md:hidden border-t border-neutral-100 px-4 py-2 space-x-2 bg-neutral-50">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex-1 flex items-center justify-center space-x-1 rounded py-1 text-xs font-medium",
                isActive
                  ? "bg-black text-white"
                  : "text-neutral-600 hover:bg-neutral-200"
              )}
            >
              <Icon className="h-3 w-3" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </header>
  );
}

