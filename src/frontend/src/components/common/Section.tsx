interface SectionProps {
  children: React.ReactNode;
  bg?: "cream" | "white" | "parchment";
  className?: string;
  id?: string;
}

const bgMap = {
  cream: "bg-cream",
  white: "bg-warm-white",
  parchment: "bg-parchment",
};

export default function Section({
  children,
  bg = "cream",
  className = "",
  id,
}: SectionProps) {
  return (
    <section id={id} className={`py-20 md:py-24 ${bgMap[bg]} ${className}`}>
      {children}
    </section>
  );
}
