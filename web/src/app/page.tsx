"use client";

import { Navbar } from "@/components/landing/Navbar";
import { Hero } from "@/components/landing/Hero";
import { Stats } from "@/components/landing/Stats";
import { Features } from "@/components/landing/Features";
import { WhyUs } from "@/components/landing/WhyUs";
import { Testimonials } from "@/components/landing/Testimonials";
import { CTA } from "@/components/landing/CTA";
import { Footer } from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <div className="landing min-h-screen overflow-x-hidden bg-canvas text-ink antialiased">
      <Navbar />
      <main>
        <Hero />
        <Stats />
        <Features />
        <WhyUs />
        <Testimonials />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}
