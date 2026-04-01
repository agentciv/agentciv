/**
 * Animation frame hook for smooth canvas rendering.
 *
 * Manages a requestAnimationFrame loop and calculates animation progress
 * (0.0 to 1.0) based on elapsed time since the last tick event.
 */

import { useEffect, useRef, useCallback } from "react";

/**
 * @param callback – called on every animation frame with the current
 *   interpolation progress (0..1).  The value resets to 0 when
 *   `resetProgress` is called (i.e. on a new tick).
 * @param tickInterval – expected milliseconds between ticks.  Progress is
 *   clamped to 1.0 so it never exceeds 1 even if a tick is late.
 */
export function useAnimation(
  callback: (progress: number) => void,
  tickInterval: number,
) {
  const rafRef = useRef<number>(0);
  const tickStartRef = useRef<number>(performance.now());
  const callbackRef = useRef(callback);
  callbackRef.current = callback;
  const intervalRef = useRef(tickInterval);
  intervalRef.current = tickInterval;

  /** Call this when a new tick arrives to reset the interpolation clock. */
  const resetProgress = useCallback(() => {
    tickStartRef.current = performance.now();
  }, []);

  useEffect(() => {
    let running = true;

    const loop = () => {
      if (!running) return;
      const elapsed = performance.now() - tickStartRef.current;
      const progress = Math.min(elapsed / intervalRef.current, 1.0);
      callbackRef.current(progress);
      rafRef.current = requestAnimationFrame(loop);
    };

    rafRef.current = requestAnimationFrame(loop);

    return () => {
      running = false;
      cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return { resetProgress };
}
