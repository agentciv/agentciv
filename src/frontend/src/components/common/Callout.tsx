interface CalloutProps {
  children: React.ReactNode;
  variant?: "gold" | "sage" | "sky";
}

const variantMap = {
  gold: "bg-gold-pale border-gold-light",
  sage: "bg-sage-pale border-sage-light",
  sky: "bg-sky-pale border-sky-light",
};

export default function Callout({ children, variant = "gold" }: CalloutProps) {
  return (
    <div
      className={`rounded-xl border p-6 ${variantMap[variant]} my-6 leading-relaxed text-ink`}
    >
      {children}
    </div>
  );
}
