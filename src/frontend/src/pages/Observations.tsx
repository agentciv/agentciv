import { Link } from "react-router-dom";
import Section from "../components/common/Section";
import Container from "../components/common/Container";

/* ---------- "What to look for" static guide ---------- */
const observationGuide = [
  {
    title: "Social patterns",
    items: [
      "Do agents cluster, or spread out? Watch for groups forming around resource zones and whether agents return to the same neighbours.",
      "Do conversations develop patterns? Some agents may become information hubs. Others may avoid interaction entirely.",
      "Does cooperation emerge without instruction? Watch for resource sharing, coordinated movement, or agents waiting for each other.",
    ],
  },
  {
    title: "Building patterns",
    items: [
      "Where do the first structures appear? Near resources, near other agents, or in isolation?",
      "Do agents build for themselves or for shared benefit? Watch for storage placed where others can use it, or shelters near common routes.",
      "Do structures cluster into settlement-like areas, or remain scattered?",
    ],
  },
  {
    title: "Innovation",
    items: [
      "When an agent proposes something entirely new, what problem was it solving? Innovation is usually a response to a specific pressure.",
      "Does knowledge of new recipes spread? Watch for whether the discoverer teaches others or keeps the knowledge.",
    ],
  },
  {
    title: "Governance",
    items: [
      "Do agents propose rules? What triggers the first rule proposal?",
      "Do other agents accept or ignore proposed rules? Watch for the difference between a rule existing and a rule being followed.",
      "Do competing rules emerge in different areas of the world?",
    ],
  },
  {
    title: "Environmental dynamics",
    items: [
      "Watch for resource depletion around busy areas. Agents may need to migrate when they exhaust local resources.",
      "Environmental shifts change the landscape. Watch how agents adapt — or fail to adapt — when their established patterns are disrupted.",
    ],
  },
];

/* ---------- Component ---------- */
export default function Observations() {
  return (
    <>
      {/* Hero */}
      <Section bg="cream" className="py-16 md:py-20">
        <Container narrow>
          <h1 className="mb-6">Observations</h1>
          <p className="text-lg leading-relaxed text-ink-light">
            The fishbowl rewards patient observation. This page is a guide to
            what is worth watching for — patterns, dynamics, and moments of
            genuine emergence.
          </p>
        </Container>
      </Section>

      {/* ================================================================
          PART 1 — WHAT TO LOOK FOR (static guide)
          ================================================================ */}
      <Section bg="white">
        <Container narrow>
          <h2 className="mb-8">What To Look For</h2>
          <p className="mb-10 leading-relaxed text-ink-light">
            The civilisation produces the most interesting dynamics when you
            know what to watch for. Here are the patterns worth paying attention
            to.
          </p>

          <div className="space-y-10">
            {observationGuide.map((category) => (
              <div key={category.title}>
                <h3 className="mb-4 text-xl">{category.title}</h3>
                <ul className="space-y-3">
                  {category.items.map((item, i) => (
                    <li
                      key={i}
                      className="flex gap-3 leading-relaxed text-ink-light"
                    >
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Container>
      </Section>

      {/* ================================================================
          PART 2 — WHERE TO OBSERVE
          ================================================================ */}
      <Section bg="parchment">
        <Container narrow className="text-center">
          <h2 className="mb-4">Watch It Happen</h2>
          <p className="mb-8 leading-relaxed text-ink-light">
            The full history of the civilisation is in the fishbowl — every
            tick, every decision, every conversation. The Chronicle tab
            records milestones, observations, and ethical flags as the world
            develops.
          </p>
          <Link
            to="/fishbowl"
            className="inline-block rounded-full bg-sky px-8 py-3 font-semibold text-white shadow-md transition-all hover:shadow-lg hover:bg-sky/90"
          >
            Watch Sim
          </Link>
        </Container>
      </Section>
    </>
  );
}
