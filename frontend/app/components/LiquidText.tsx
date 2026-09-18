"use client";

import { CSSProperties, useState } from "react";

type LiquidTextProps = {
  children: string;
  className?: string;
  as?: "span" | "h1" | "h2" | "p";
};

export default function LiquidText({ children, className = "", as = "span" }: LiquidTextProps) {
  const [isActive, setIsActive] = useState(false);
  const Tag = as;

  return (
    <Tag
      className={`liquid-text-interactive ${className}`}
      data-liquid-active={isActive}
      onPointerEnter={() => setIsActive(true)}
      onPointerLeave={() => setIsActive(false)}
      aria-label={children}
    >
      {children.split("").map((character, index) => {
        const style = {
          "--scatter-x": `${((index * 37) % 13) - 6}em`,
          "--scatter-y": `${((index * 19) % 9) - 4}em`,
          "--scatter-rotate": `${((index * 47) % 70) - 35}deg`,
          "--liquid-delay": `${(index % 9) * 24}ms`,
        } as CSSProperties;
        return (
          <span aria-hidden="true" className="liquid-letter" style={style} key={`${character}-${index}`}>
            {character === " " ? "\u00a0" : character}
          </span>
        );
      })}
    </Tag>
  );
}
