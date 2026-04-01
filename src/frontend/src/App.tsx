import { useEffect } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Home from "./pages/Home";
import HowItWorks from "./pages/HowItWorks";
import TheScience from "./pages/TheScience";
import Ethics from "./pages/Ethics";
import Observations from "./pages/Observations";
import OpenSource from "./pages/OpenSource";
import About from "./pages/About";
import Simulations from "./pages/Simulations";
import Whitepaper from "./pages/Whitepaper";
import Fishbowl from "./pages/Fishbowl";
import Methodology from "./pages/Methodology";
import SimDiscovery from "./pages/SimDiscovery";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        {/* Information pages — standard layout with nav + footer */}
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/how-it-works" element={<HowItWorks />} />
          <Route path="/science" element={<TheScience />} />
          <Route path="/ethics" element={<Ethics />} />
          <Route path="/observations" element={<Observations />} />
          <Route path="/open-source" element={<OpenSource />} />
          <Route path="/simulations" element={<Simulations />} />
          <Route path="/whitepaper" element={<Whitepaper />} />
          <Route path="/methodology" element={<Methodology />} />
          <Route path="/discovery" element={<SimDiscovery />} />
          <Route path="/about" element={<About />} />
        </Route>

        {/* Fishbowl — full-screen layout, no standard nav/footer */}
        <Route path="/fishbowl" element={<Fishbowl />} />
      </Routes>
    </>
  );
}
