"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/landing/Logo";
import { cn } from "@/lib/utils";

const links = [
  { href: "#features", label: "Features" },
  { href: "#why-carry", label: "Why Carry" },
  { href: "#testimonials", label: "Customers" },
];

export function Navbar() {
  const [open, setOpen] = useState(false);
  const reducedMotion = useReducedMotion();

  return (
    <motion.header
      initial={reducedMotion ? false : { opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="fixed inset-x-0 top-0 z-50 border-b border-line/60 bg-canvas/70 backdrop-blur-xl"
    >
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Logo />

        <div className="hidden items-center gap-1 md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-md px-3 py-2 text-small font-medium text-ink-secondary transition-colors hover:bg-panel hover:text-ink"
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <Link
            href="/sign-in"
            className="text-small font-medium text-ink-secondary transition-colors hover:text-ink"
          >
            Sign in
          </Link>
          <Link href="/sign-up">
            <Button className="btn-glow gap-1.5">
              Get Started
              <ArrowRight className="size-4" />
            </Button>
          </Link>
        </div>

        <Button
          variant="ghost"
          size="icon-sm"
          className="text-ink-secondary md:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label={open ? "Close menu" : "Open menu"}
        >
          {open ? <X className="size-4" /> : <Menu className="size-4" />}
        </Button>
      </nav>

      <div
        className={cn(
          "overflow-hidden border-t border-line/60 bg-canvas/90 backdrop-blur-xl transition-[max-height,opacity] duration-300 md:hidden",
          open ? "max-h-72 opacity-100" : "max-h-0 opacity-0"
        )}
      >
        <div className="flex flex-col gap-1 px-4 py-4">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className="rounded-md px-3 py-2.5 text-body font-medium text-ink-secondary transition-colors hover:bg-panel hover:text-ink"
            >
              {link.label}
            </Link>
          ))}
          <div className="mt-2 flex items-center gap-3 border-t border-line/60 pt-3">
            <Link href="/search" className="flex-1">
              <Button variant="outline" size="sm" className="w-full">
                Sign in
              </Button>
            </Link>
            <Link href="/search" className="flex-1">
              <Button size="sm" className="btn-glow w-full gap-1.5">
                Get Started
                <ArrowRight className="size-4" />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </motion.header>
  );
}
