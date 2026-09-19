"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import Image from "next/image";

export default function LandingPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return <div style={{ minHeight: "100vh", backgroundColor: "#000" }} />;

  return (
    <div style={{ 
      minHeight: "100vh", 
      backgroundColor: "#000", 
      color: "#fff", 
      fontFamily: "var(--font-sans)",
      overflow: "hidden",
      position: "relative"
    }}>
      
      {/* Top Navbar */}
      <nav style={{ 
        position: "absolute", 
        top: 0, left: 0, right: 0, 
        padding: "24px 48px", 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center", 
        zIndex: 50 
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
          <div style={{ display: "flex", gap: 10, alignItems: "center", fontWeight: 700, fontSize: 18, letterSpacing: "-0.04em" }}>
            <img src="/ArgusCX.png" alt="ArgusCX Logo" style={{ width: 24, height: 24, filter: "drop-shadow(0 0 8px rgba(155, 231, 197, 0.4))" }} />
            ArgusCX
          </div>
          <div style={{ display: "flex", gap: 24, fontSize: 13, color: "#888", fontWeight: 500 }}>
            <span style={{ cursor: "pointer", transition: "color 0.2s" }} onMouseEnter={e => e.currentTarget.style.color = "#fff"} onMouseLeave={e => e.currentTarget.style.color = "#888"}>Product</span>
            <span style={{ cursor: "pointer", transition: "color 0.2s" }} onMouseEnter={e => e.currentTarget.style.color = "#fff"} onMouseLeave={e => e.currentTarget.style.color = "#888"}>Infrastructure</span>
            <span style={{ cursor: "pointer", transition: "color 0.2s" }} onMouseEnter={e => e.currentTarget.style.color = "#fff"} onMouseLeave={e => e.currentTarget.style.color = "#888"}>Enterprise</span>
          </div>
        </div>
        
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <Link href="/login" style={{ 
            fontSize: 13, 
            padding: "8px 16px", 
            border: "1px solid #333", 
            borderRadius: 6,
            color: "#fff",
            textDecoration: "none",
            transition: "all 0.2s",
            background: "rgba(255,255,255,0.03)"
          }} onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.08)"} onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,0.03)"}>
            Dashboard
          </Link>
          <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(45deg, #9BE7C5, #b58cff)" }} />
        </div>
      </nav>

      {/* Main Hero Section */}
      <main style={{ 
        height: "100vh", 
        display: "flex", 
        alignItems: "center", 
        justifyContent: "space-between",
        padding: "0 10vw",
        position: "relative",
        zIndex: 10
      }}>
        
        {/* Left Typography */}
        <div style={{ zIndex: 20, maxWidth: 500 }}>
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            style={{ 
              fontSize: "clamp(56px, 6vw, 84px)", 
              fontWeight: 500, 
              letterSpacing: "-0.05em",
              lineHeight: 0.95,
              marginBottom: 32
            }}
          >
            Autonomous <br/> Infrastructure
          </motion.h1>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
            style={{ display: "flex", gap: 16 }}
          >
            <Link href="/login" style={{ 
              background: "#fff", 
              color: "#000",
              padding: "12px 24px",
              borderRadius: 30,
              fontSize: 14,
              fontWeight: 500,
              textDecoration: "none",
              display: "flex",
              alignItems: "center",
              gap: 8,
              transition: "transform 0.2s"
            }} onMouseEnter={e => e.currentTarget.style.transform = "scale(1.02)"} onMouseLeave={e => e.currentTarget.style.transform = "scale(1)"}>
              Deploy now <ArrowRight size={16} />
            </Link>
            <Link href="/login" style={{ 
              background: "transparent", 
              color: "#fff",
              border: "1px solid #333",
              padding: "12px 24px",
              borderRadius: 30,
              fontSize: 14,
              fontWeight: 500,
              textDecoration: "none",
              transition: "background 0.2s"
            }} onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.05)"} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
              Talk to sales
            </Link>
          </motion.div>
        </div>

        {/* Center Glowing ARGUS LENS Effect */}
        <div style={{ position: "absolute", left: "50%", top: "50%", transform: "translate(-50%, -50%)", width: 500, height: 500, zIndex: 10, display: "flex", alignItems: "center", justifyContent: "center" }}>
          
          {/* Animated Glow Layers (Argus Brand Colors) */}
          <motion.div 
            animate={{ rotate: 360, scale: [1, 1.1, 1] }} 
            transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
            style={{ position: "absolute", width: "90%", height: "90%", background: "radial-gradient(circle, rgba(155, 231, 197, 0.4) 0%, transparent 60%)", filter: "blur(70px)", mixBlendMode: "screen" }}
          />
          <motion.div 
            animate={{ rotate: -360, scale: [1, 1.2, 1] }} 
            transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
            style={{ position: "absolute", width: "100%", height: "100%", background: "radial-gradient(circle, rgba(181, 140, 255, 0.35) 0%, transparent 60%)", filter: "blur(80px)", mixBlendMode: "screen" }}
          />
          
          {/* Outer Lens Ring */}
          <motion.div 
            animate={{ rotate: 360 }} 
            transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
            style={{ 
              position: "absolute", width: 280, height: 280, borderRadius: "50%",
              border: "1px solid rgba(155, 231, 197, 0.1)",
              borderTopColor: "rgba(181, 140, 255, 0.8)",
              borderBottomColor: "rgba(155, 231, 197, 0.8)",
              boxShadow: "inset 0 0 30px rgba(155, 231, 197, 0.05), 0 0 40px rgba(181, 140, 255, 0.1)",
              zIndex: 15
            }} 
          />

          {/* Inner Lens Ring */}
          <motion.div 
            animate={{ rotate: -360 }} 
            transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
            style={{ 
              position: "absolute", width: 180, height: 180, borderRadius: "50%",
              border: "2px dashed rgba(255, 255, 255, 0.1)",
              borderLeft: "2px solid rgba(155, 231, 197, 0.9)",
              zIndex: 16
            }} 
          />

          {/* Core Eye / Logo Container */}
          <div style={{ 
            position: "absolute", 
            width: 120, height: 120, 
            borderRadius: "50%",
            background: "#000",
            boxShadow: "inset 0 0 20px rgba(255,255,255,0.1), 0 0 50px rgba(155, 231, 197, 0.3)",
            zIndex: 20,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            overflow: "hidden"
          }}>
            <img src="/ArgusCX.png" alt="Argus" style={{ width: 64, height: 64, objectFit: "contain", filter: "drop-shadow(0 0 15px rgba(155,231,197,0.8))" }} />
          </div>

          {/* Core intense light right behind the logo */}
          <div style={{
            position: "absolute", width: 150, height: 150,
            background: "radial-gradient(circle, rgba(255,255,255,0.9) 0%, transparent 70%)",
            filter: "blur(25px)",
            zIndex: 14
          }} />
        </div>

        {/* Right Feature List */}
        <div style={{ zIndex: 20, width: 200, display: "flex", flexDirection: "column", gap: 16 }}>
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8, delay: 0.2 }}>
            <p style={{ fontSize: 13, fontWeight: 500, color: "#e0e0e0", margin: 0 }}>For claims agents</p>
          </motion.div>
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8, delay: 0.3 }}>
            <p style={{ fontSize: 13, fontWeight: 500, color: "#e0e0e0", margin: 0 }}>To verify claims automatically</p>
          </motion.div>
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8, delay: 0.4 }}>
            <p style={{ fontSize: 13, fontWeight: 500, color: "#e0e0e0", margin: 0 }}>Secured by AI forensics</p>
          </motion.div>
        </div>
      </main>

      {/* Footer Brands */}
      <footer style={{ 
        position: "absolute", 
        bottom: 0, left: 0, right: 0, 
        padding: "40px", 
        display: "flex", 
        justifyContent: "center", 
        alignItems: "center",
        gap: "6vw",
        opacity: 0.5,
        filter: "grayscale(100%)",
        zIndex: 50
      }}>
        <div style={{ fontSize: 18, fontWeight: 800, letterSpacing: "-0.05em" }}>Shopify</div>
        <div style={{ fontSize: 18, fontWeight: 500, letterSpacing: "-0.02em" }}>Zendesk</div>
        <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: "0em", fontStyle: "italic" }}>Stripe</div>
        <div style={{ fontSize: 18, fontWeight: 600, letterSpacing: "-0.04em" }}>Gorgias</div>
        <div style={{ fontSize: 18, fontWeight: 400, letterSpacing: "0.1em", textTransform: "uppercase" }}>Salesforce</div>
      </footer>
    </div>
  );
}
