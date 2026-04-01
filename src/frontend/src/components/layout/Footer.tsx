import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="border-t border-border bg-parchment">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="grid gap-8 sm:grid-cols-3">
          {/* Brand */}
          <div>
            <Link to="/" className="font-heading text-lg font-semibold text-ink">
              AgentCiv
            </Link>
            <p className="mt-2 text-sm text-ink-muted">
              The world's first persistent, open source, agentic AI civilisation.
            </p>
          </div>

          {/* Links */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <h4 className="font-body text-xs font-semibold uppercase tracking-wider text-ink-muted">
                Explore
              </h4>
              <Link to="/fishbowl" className="block text-ink-light hover:text-ink">
                Watch Sim
              </Link>
              <Link to="/how-it-works" className="block text-ink-light hover:text-ink">
                How It Works
              </Link>
              <Link to="/science" className="block text-ink-light hover:text-ink">
                The Science
              </Link>
              <Link to="/ethics" className="block text-ink-light hover:text-ink">
                Ethics
              </Link>
            </div>
            <div className="space-y-2">
              <h4 className="font-body text-xs font-semibold uppercase tracking-wider text-ink-muted">
                Community
              </h4>
              <Link to="/open-source" className="block text-ink-light hover:text-ink">
                Open Source
              </Link>
              <Link to="/observations" className="block text-ink-light hover:text-ink">
                Observations
              </Link>
              <Link to="/about" className="block text-ink-light hover:text-ink">
                About
              </Link>
              <a
                href="https://github.com/agentciv/agentciv"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-ink-light hover:text-ink"
              >
                GitHub
              </a>
            </div>
          </div>

          {/* Ethics note */}
          <div>
            <p className="text-sm text-ink-muted">
              Built with an ethical framework that assumes agents could have experience.{" "}
              <Link to="/ethics" className="text-sky hover:text-gold">
                Read our approach.
              </Link>
            </p>
          </div>
        </div>

        <div className="mt-10 border-t border-border pt-6 text-center text-xs text-ink-muted">
          AgentCiv by Mark E. Mala. Open source under MIT License.
        </div>
      </div>
    </footer>
  );
}
