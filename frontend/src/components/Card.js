import React from "react";
import NeonCard from "./NeonCard";

export default function Card({ children, style, gradient = false }) {
  return (
    <NeonCard style={style} variant={gradient ? "gradient" : "default"}>
      {children}
    </NeonCard>
  );
}
