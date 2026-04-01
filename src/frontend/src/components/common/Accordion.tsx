import { useState } from "react";

interface AccordionItem {
  question: string;
  answer: string;
}

interface AccordionProps {
  items: AccordionItem[];
}

function AccordionRow({ question, answer }: AccordionItem) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-border">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between py-5 text-left"
      >
        <span className="pr-4 font-heading text-lg font-medium text-ink">
          {question}
        </span>
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className={`shrink-0 text-ink-muted transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
        >
          <path d="M5 7.5L10 12.5L15 7.5" />
        </svg>
      </button>
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          open ? "max-h-[1000px] pb-5" : "max-h-0"
        }`}
      >
        <p className="leading-relaxed text-ink-light">{answer}</p>
      </div>
    </div>
  );
}

export default function Accordion({ items }: AccordionProps) {
  return (
    <div className="divide-y-0">
      {items.map((item, i) => (
        <AccordionRow key={i} {...item} />
      ))}
    </div>
  );
}
