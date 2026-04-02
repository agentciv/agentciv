import { useEffect, lazy, Suspense } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Home from "./pages/Home";

// Lazy-load heavier pages (chart-heavy / data-heavy) for code splitting
const SimDiscovery = lazy(() => import("./pages/SimDiscovery"));
const Simulations = lazy(() => import("./pages/Simulations"));
const Interviews = lazy(() => import("./pages/Interviews"));
const DataExplorer = lazy(() => import("./pages/DataExplorer"));
const Fishbowl = lazy(() => import("./pages/Fishbowl"));
const TheJourney = lazy(() => import("./pages/TheJourney"));
const Highlights = lazy(() => import("./pages/Highlights"));

// Lighter pages — direct imports
import HowItWorks from "./pages/HowItWorks";
import TheScience from "./pages/TheScience";
import Ethics from "./pages/Ethics";
import Observations from "./pages/Observations";
import OpenSource from "./pages/OpenSource";
import About from "./pages/About";
import Whitepaper from "./pages/Whitepaper";
import Methodology from "./pages/Methodology";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

function PageLoader() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <p className="text-sm text-ink-muted">Loading...</p>
    </div>
  );
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Information pages — standard layout with nav + footer */}
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/highlights" element={<Highlights />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/science" element={<TheScience />} />
            <Route path="/ethics" element={<Ethics />} />
            <Route path="/observations" element={<Observations />} />
            <Route path="/open-source" element={<OpenSource />} />
            <Route path="/simulations" element={<Simulations />} />
            <Route path="/whitepaper" element={<Whitepaper />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/discovery" element={<SimDiscovery />} />
            <Route path="/interviews" element={<Interviews />} />
            <Route path="/explorer" element={<DataExplorer />} />
            <Route path="/journey" element={<TheJourney />} />
            <Route path="/about" element={<About />} />
          </Route>

          {/* Fishbowl — full-screen layout, no standard nav/footer */}
          <Route path="/fishbowl" element={<Fishbowl />} />
        </Routes>
      </Suspense>
    </>
  );
}
