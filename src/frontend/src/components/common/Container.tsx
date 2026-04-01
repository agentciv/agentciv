interface ContainerProps {
  children: React.ReactNode;
  narrow?: boolean;
  className?: string;
}

export default function Container({
  children,
  narrow = false,
  className = "",
}: ContainerProps) {
  return (
    <div
      className={`mx-auto px-6 ${narrow ? "max-w-3xl" : "max-w-7xl"} ${className}`}
    >
      {children}
    </div>
  );
}
