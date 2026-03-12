"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Users,
  FileText,
  Settings,
  Droplets,
  CalendarDays,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/leads", label: "Leads", icon: Users },
  { href: "/estimates", label: "Estimates", icon: FileText },
  { href: "/schedule", label: "Schedule", icon: CalendarDays },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 min-h-screen flex flex-col" style={{ background: "#111827" }}>
      {/* Logo / Brand */}
      <div className="px-6 py-5 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div
            className="h-8 w-8 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: "#0693e3" }}
          >
            <Droplets className="h-4 w-4 text-white" />
          </div>
          <div>
            <p className="font-bold text-sm text-white leading-none">A&T's Pressure</p>
            <p className="text-xs mt-0.5" style={{ color: "#8ed1fc" }}>Washing Dashboard</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "text-white"
                  : "text-gray-400 hover:text-white hover:bg-white/8"
              )}
              style={isActive ? { background: "#0693e3" } : undefined}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-white/10">
        <p className="text-xs" style={{ color: "#6b7280" }}>A&T's Pressure Washing</p>
        <p className="text-xs mt-0.5" style={{ color: "#4b5563" }}>Fence Restoration Division</p>
      </div>
    </aside>
  );
}
