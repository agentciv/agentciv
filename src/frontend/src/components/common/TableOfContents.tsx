import { useEffect, useState } from "react";

interface TocItem {
  id: string;
  label: string;
}

interface TableOfContentsProps {
  items: TocItem[];
}

export default function TableOfContents({ items }: TableOfContentsProps) {
  const [activeId, setActiveId] = useState<string>("");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        // Find the first entry that is intersecting
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible.length > 0) {
          setActiveId(visible[0].target.id);
        }
      },
      {
        rootMargin: "-80px 0px -60% 0px",
        threshold: 0,
      }
    );

    items.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [items]);

  return (
    <nav className="hidden lg:block">
      <div className="sticky top-24 space-y-1">
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-ink-muted">
          On this page
        </p>
        {items.map(({ id, label }) => (
          <a
            key={id}
            href={`#${id}`}
            className={`block rounded-lg px-3 py-1.5 text-sm transition-colors ${
              activeId === id
                ? "bg-gold-pale font-medium text-ink"
                : "text-ink-muted hover:text-ink-light"
            }`}
          >
            {label}
          </a>
        ))}
      </div>
    </nav>
  );
}
