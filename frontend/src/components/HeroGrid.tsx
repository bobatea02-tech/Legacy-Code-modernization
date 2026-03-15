const HeroGrid = () => {
  const words = ["MOD", "ERN", "IZE", "NOW"];

  return (
    <section className="h-screen pt-[72px] grid grid-cols-2 grid-rows-2">
      {words.map((word, i) => (
        <div
          key={word}
          className={`relative flex items-end p-6 overflow-hidden
            ${i % 2 === 0 ? "hairline-r" : ""}
            ${i < 2 ? "hairline-b" : ""}
          `}
        >
          <span
            className="font-headline text-foreground leading-[0.85] uppercase"
            style={{
              fontSize: "clamp(5rem, 18vw, 24vw)",
              letterSpacing: "-0.06em",
            }}
          >
            {word}
          </span>
        </div>
      ))}
    </section>
  );
};

export default HeroGrid;
