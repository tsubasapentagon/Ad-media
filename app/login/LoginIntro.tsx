"use client";

import { useEffect, useState } from "react";

export function LoginIntro() {
  const [visible, setVisible] = useState(true);
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const leaveTimer = window.setTimeout(() => setLeaving(true), reducedMotion ? 350 : 2350);
    const removeTimer = window.setTimeout(() => setVisible(false), reducedMotion ? 650 : 2950);
    return () => {
      window.clearTimeout(leaveTimer);
      window.clearTimeout(removeTimer);
    };
  }, []);

  function skip() {
    setLeaving(true);
    window.setTimeout(() => setVisible(false), 450);
  }

  if (!visible) return null;
  return <div className={`login-intro${leaving ? " leaving" : ""}`} aria-label="小林広告分析 ver.2" aria-live="polite">
    <div className="login-intro-mark" aria-hidden="true"><span>K</span><i/><i/><i/></div>
    <div className="login-intro-copy">
      <div className="login-intro-title"><strong>小林広告分析</strong><em>ver.2</em></div>
      <svg viewBox="0 0 420 16" aria-hidden="true"><path pathLength="1" d="M7 9 C75 3 133 13 207 7 C278 2 345 12 413 6"/></svg>
      <p>MEDIA PERFORMANCE ANALYTICS</p>
    </div>
    <button type="button" onClick={skip}>スキップ</button>
  </div>;
}
