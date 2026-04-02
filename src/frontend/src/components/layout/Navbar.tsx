import { Link, NavLink } from "react-router-dom";

const navItems = [
  { to: "/highlights", label: "Highlights" },
  { to: "/discovery", label: "Findings" },
  { to: "/simulations", label: "Data" },
  { to: "/interviews", label: "Interviews" },
  { to: "/explorer", label: "Explorer" },
  { to: "/how-it-works", label: "How It Works" },
  { to: "/journey", label: "The Journey" },
  { to: "/methodology", label: "Methodology" },
  { to: "/science", label: "The Science" },
  { to: "/whitepaper", label: "Papers" },
  { to: "/ethics", label: "Ethics" },
  { to: "/open-source", label: "Open Source" },
];

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-cream/90 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        {/* Logo */}
        <Link to="/" className="font-heading text-xl font-semibold text-ink">
          AgentCiv
        </Link>

        {/* Desktop nav */}
        <div className="hidden items-center gap-1 md:flex">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-gold-pale text-ink"
                    : "text-ink-light hover:bg-parchment hover:text-ink"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}

          {/* The Fishbowl — accent CTA */}
          <NavLink
            to="/fishbowl"
            className={({ isActive }) =>
              `ml-3 rounded-full px-5 py-2 text-sm font-semibold transition-all ${
                isActive
                  ? "bg-sky text-white shadow-md"
                  : "bg-sky text-white shadow-sm hover:bg-sky/90 hover:shadow-md"
              }`
            }
          >
            Watch Sim
          </NavLink>
        </div>

        {/* Mobile menu button */}
        <button
          className="flex items-center justify-center rounded-lg p-2 text-ink-light hover:bg-parchment md:hidden"
          aria-label="Menu"
          onClick={() => {
            const menu = document.getElementById("mobile-menu");
            if (menu) menu.classList.toggle("hidden");
          }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 12h18M3 6h18M3 18h18" />
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      <div id="mobile-menu" className="hidden border-t border-border bg-cream px-6 pb-4 md:hidden">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `block rounded-lg px-3 py-2.5 text-sm font-medium ${
                isActive ? "bg-gold-pale text-ink" : "text-ink-light"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
        <NavLink
          to="/fishbowl"
          className="mt-2 block rounded-full bg-sky px-5 py-2.5 text-center text-sm font-semibold text-white"
        >
          Watch Sim
        </NavLink>
      </div>
    </nav>
  );
}
