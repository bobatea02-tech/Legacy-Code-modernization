import { useState } from "react";

const GeometricCard = () => {
  const [hovered, setHovered] = useState(false);

  return (
    <section className="flex items-center justify-center py-24 px-6">
      <div
        className="w-[300px] h-[300px] hairline flex items-center justify-center cursor-pointer"
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        <div
          className="w-[180px] h-[180px] hairline transition-transform"
          style={{
            transform: hovered ? "rotate(90deg)" : "rotate(45deg)",
            transitionDuration: "700ms",
            transitionTimingFunction: "cubic-bezier(0.4, 0, 0.2, 1)",
          }}
        />
      </div>
    </section>
  );
};

export default GeometricCard;
