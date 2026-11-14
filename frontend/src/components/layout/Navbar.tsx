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
      label: "Approvals",
      href: "/approvals",
      icon: ShieldCheck,
    },
    {
      label: "Knowledge Base",
      href: "/knowledge-base",
      icon: BookOpen,
    },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[#E5E7EB] bg-white">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center space-x-6">
          <Link href="/events" className="flex items-center space-x-2 font-bold tracking-tight text-[#111111] text-sm">
            <span className="flex h-6 w-6 items-center justify-center rounded-sm bg-[#111111] text-white text-xs font-black">
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
                      ? "bg-[#111111] text-white"
                      : "text-[#6B7280] hover:bg-[#F5F5F5] hover:text-[#111111]"
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
          <div className="flex items-center space-x-1.5 text-xs text-[#333333] border border-[#E5E7EB] rounded-md px-2.5 py-1 bg-[#F5F5F5]">
            <ShieldCheck className="h-3.5 w-3.5 text-[#111111]" />
            <span className="font-mono">{user || "admin"}</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            className="text-xs text-[#6B7280] hover:text-[#111111] hover:bg-[#F5F5F5] border border-transparent hover:border-[#E5E7EB] h-8 px-2.5 transition-colors"
          >
            <LogOut className="mr-1.5 h-3.5 w-3.5" />
            Logout
          </Button>
        </div>
      </div>

      {/* Mobile nav */}
      <div className="flex md:hidden border-t border-[#E5E7EB] px-4 py-2 space-x-2 bg-[#F5F5F5]">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex-1 flex items-center justify-center space-x-1 rounded py-1 text-xs font-medium transition-colors",
                isActive
                  ? "bg-[#111111] text-white"
                  : "text-[#6B7280] hover:bg-[#E5E7EB] hover:text-[#111111]"
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
