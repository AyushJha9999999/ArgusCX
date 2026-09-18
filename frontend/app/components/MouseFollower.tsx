"use client";

import { useEffect, useRef } from "react";

export default function MouseFollower() {
  const followerRef = useRef<HTMLDivElement>(null);
  const target = useRef({ x: -200, y: -200 });
  const current = useRef({ x: -200, y: -200 });

  useEffect(() => {
    let frame = 0;
    const onPointerMove = (event: PointerEvent) => {
      target.current = { x: event.clientX, y: event.clientY };
    };
    const onPointerOver = (event: PointerEvent) => {
      const element = event.target as HTMLElement;
      followerRef.current?.setAttribute("data-hovering", String(Boolean(element.closest("a, button, [role='button']"))));
    };
    const animate = () => {
      current.current.x += (target.current.x - current.current.x) * 0.16;
      current.current.y += (target.current.y - current.current.y) * 0.16;
      followerRef.current?.style.setProperty("transform", `translate3d(${current.current.x}px, ${current.current.y}px, 0)`);
      frame = requestAnimationFrame(animate);
    };

    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("pointerover", onPointerOver, { passive: true });
    frame = requestAnimationFrame(animate);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerover", onPointerOver);
    };
  }, []);

  return (
    <div
      aria-hidden="true"
      className="mouse-follower"
      ref={followerRef}
    />
  );
}
