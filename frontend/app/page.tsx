"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────
type Panel = "none" | "score" | "history" | "actions" | "support";
type OrbState = "idle" | "listening" | "thinking";

interface ArthScore {
  score: number;
  band: string;
  next_best_action?: string;
  savings_rate?: number;
  debt_ratio?: number;
}

interface HistoryEntry {
  id: string;
  query: string;
  response: string;
  intent: string;
  scamDetected: boolean;
  schemes: SchemeItem[];
  score: ArthScore | null;
  timestamp: number;
}

interface SchemeItem {
  name: string;
  description?: string;
  eligibility?: string;
  tags?: string[];
}

interface UserProfile {
  user_id: string;
  name: string;
  language: string;
  occupation: string;
  age: number;
  monthly_income_inr: number;
  monthly_expenses_inr: number;
  emergency_fund_inr: number;
  monthly_debt_emi_inr: number;
  has_bank_account: boolean;
  has_disability: boolean;
  land_ownership: boolean;
  has_daughter_below_10: boolean;
  not_epf_member: boolean;
}

// ─── Constants ────────────────────────────────────────────────────────────────
const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const DEFAULT_USER_ID = "voice-user";

const LANGUAGES = [
  { code: "hi", label: "हिंदी" },
  { code: "en", label: "English" },
  { code: "mr", label: "मराठी" },
  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" },
  { code: "bn", label: "বাংলা" },
  { code: "gu", label: "ગુજરાતી" },
  { code: "pa", label: "ਪੰਜਾਬੀ" },
];

const BAND_CLASS: Record<string, string> = {
  urgent_support: "band-urgent",
  fragile: "band-fragile",
  improving: "band-improving",
  stable: "band-stable",
};

const BAND_COLOR: Record<string, string> = {
  urgent_support: "#e53e3e",
  fragile: "#f6ad55",
  improving: "#63b3ed",
  stable: "#48bb78",
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
function formatTime(ts: number) {
  const d = new Date(ts);
  return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

function now() {
  return new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

// Speak text via browser TTS (respects global mute)
let _isMuted = false;
function speak(text: string, lang: string) {
  if (_isMuted) return;
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  const langMap: Record<string, string> = {
    hi: "hi-IN", en: "en-IN", mr: "mr-IN", kn: "kn-IN",
    ta: "ta-IN", te: "te-IN", bn: "bn-IN", gu: "gu-IN", pa: "pa-IN",
  };
  utt.lang = langMap[lang] || "hi-IN";
  utt.rate = 0.9;
  window.speechSynthesis.speak(utt);
}
function stopSpeaking() {
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
}

// ─── Animated Waveform Canvas ─────────────────────────────────────────────────
function useWaveform(canvasRef: React.RefObject<HTMLCanvasElement | null>, active: boolean) {
  const rafRef = useRef<number | null>(null);
  const bars = useRef<number[]>(Array.from({ length: 24 }, () => Math.random() * 0.4 + 0.1));

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    function draw() {
      if (!canvas || !ctx) return;
      const W = canvas.width, H = canvas.height;
      const cx = W / 2, cy = H / 2;
      ctx.clearRect(0, 0, W, H);

      if (!active) {
        // idle: subtle flat line
        bars.current = bars.current.map(b => b * 0.9 + 0.05 * 0.1);
      } else {
        bars.current = bars.current.map(b => {
          const target = Math.random() * 0.8 + 0.15;
          return b * 0.6 + target * 0.4;
        });
      }

      const n = bars.current.length;
      const step = (Math.PI * 2) / n;
      const innerR = 70, outerMaxR = 90;

      ctx.strokeStyle = "rgba(229,62,62,0.7)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      bars.current.forEach((amp, i) => {
        const angle = step * i - Math.PI / 2;
        const r = innerR + amp * (outerMaxR - innerR);
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.stroke();

      // Soft fill
      ctx.fillStyle = "rgba(229,62,62,0.08)";
      ctx.fill();

      rafRef.current = requestAnimationFrame(draw);
    }

    rafRef.current = requestAnimationFrame(draw);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [active, canvasRef]);
}

// ─── Score Ring SVG ───────────────────────────────────────────────────────────
function ScoreRing({ score, band }: { score: number; band: string }) {
  const r = 80;
  const circ = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(score, 100)) / 100;
  const offset = circ * (1 - pct);
  const color = BAND_COLOR[band] || "#e53e3e";

  return (
    <div className="score-ring-wrap">
      <div className="score-ring">
        <svg width="180" height="180" viewBox="0 0 180 180">
          <circle className="score-ring-track" cx="90" cy="90" r={r} />
          <circle
            className="score-ring-fill"
            cx="90" cy="90" r={r}
            stroke={color}
            strokeDasharray={circ}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="score-center">
          <div className="score-number">{score}</div>
          <div className="score-denom">/100</div>
        </div>
      </div>
      <div className={`score-band ${BAND_CLASS[band] || "band-stable"}`}>
        {band?.replace(/_/g, " ") || "stable"}
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function VoiceHub() {
  const [profileReady, setProfileReady] = useState(false);
  const [profile, setProfile] = useState<UserProfile>({
    user_id: DEFAULT_USER_ID,
    name: "",
    language: "hi",
    occupation: "gig_worker",
    age: 30,
    monthly_income_inr: 0,
    monthly_expenses_inr: 0,
    emergency_fund_inr: 0,
    monthly_debt_emi_inr: 0,
    has_bank_account: true,
    has_disability: false,
    land_ownership: false,
    has_daughter_below_10: false,
    not_epf_member: true,
  });
  const [orbState, setOrbState] = useState<OrbState>("idle");
  const [transcript, setTranscript] = useState("");
  const [activePanel, setActivePanel] = useState<Panel>("none");
  const [language, setLanguage] = useState("hi");
  const [isOnline, setIsOnline] = useState(true);
  const [timeStr, setTimeStr] = useState(now());
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [currentResponse, setCurrentResponse] = useState<HistoryEntry | null>(null);
  const [showResponse, setShowResponse] = useState(false);
  const [isMuted, setIsMuted] = useState(false);

  // Smart actions state
  const [schemeResults, setSchemeResults] = useState<SchemeItem[]>([]);
  const [schemesLoaded, setSchemesLoaded] = useState(false);
  const [schemeLoading, setSchemeLoading] = useState(false);
  const [fraudCheckResult, setFraudCheckResult] = useState<string | null>(null);
  const [fraudLoading, setFraudLoading] = useState(false);
  const [scoreData, setScoreData] = useState<ArthScore | null>(null);
  const [scoreLoading, setScoreLoading] = useState(false);
  const [scoreLoaded, setScoreLoaded] = useState(false);

  // Nudge cards (only appear after real responses)
  const [nudgeCards, setNudgeCards] = useState<Array<{
    id: string; type: "scam" | "score" | "scheme" | "info"; label: string; text: string; audio?: string;
  }>>([]);

  // Swipe gesture state
  const touchStart = useRef<{ x: number; y: number } | null>(null);
  const mouseStart = useRef<{ x: number; y: number } | null>(null);

  // Waveform canvas
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  useWaveform(canvasRef, orbState === "listening");

  // Speech recognition ref
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const saved = localStorage.getItem("arthsetu_profile");
    if (!saved) return;
    try {
      const parsed = JSON.parse(saved);
      setProfile(parsed);
      setLanguage(parsed.language || "hi");
      setProfileReady(true);
    } catch {
      localStorage.removeItem("arthsetu_profile");
    }
  }, []);

  // ─── Lifecycle ──────────────────────────────────────────────────────────────
  useEffect(() => {
    const tick = setInterval(() => setTimeStr(now()), 30000);
    return () => clearInterval(tick);
  }, []);

  useEffect(() => {
    const up = () => setIsOnline(true);
    const down = () => setIsOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    setIsOnline(navigator.onLine);
    return () => { window.removeEventListener("online", up); window.removeEventListener("offline", down); };
  }, []);

  // ─── API Call ───────────────────────────────────────────────────────────────
  const callAPI = useCallback(async (message: string, profileUpdates?: Record<string, unknown>) => {
    setOrbState("thinking");
    setShowResponse(false);
    try {
      const res = await fetch(`${API}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: profile.user_id, message, profile_updates: profileUpdates || profile }),
      });
      if (!res.ok) throw new Error("API error");
      const data = await res.json();

      const scoreRaw = data.arth_score_update || data.agent_outputs?.vivek?.arth_score || null;
      const schemes: SchemeItem[] = data.scheme_matches || data.agent_outputs?.shilpi?.schemes_to_apply || [];
      const scamDet: boolean = data.scam_detected || false;
      const intent: string = data.intent || "general";
      const response: string = data.final_response || "ArthSetu processed your request.";

      const entry: HistoryEntry = {
        id: `${Date.now()}`,
        query: message,
        response,
        intent,
        scamDetected: scamDet,
        schemes,
        score: scoreRaw,
        timestamp: Date.now(),
      };

      setHistory(prev => [entry, ...prev.slice(0, 19)]);
      setCurrentResponse(entry);
      setOrbState("idle");
      setShowResponse(true);

      // Auto-speak the response
      speak(response, language);

      // Add nudge cards based on what came back
      const newNudges: typeof nudgeCards = [];
      if (scamDet) {
        newNudges.push({ id: `scam-${Date.now()}`, type: "scam", label: "⚠️ Prahari Alert", text: "Scam pattern detected in your message" });
      }
      if (scoreRaw?.score !== undefined) {
        setScoreData(scoreRaw);
        setScoreLoaded(true);
        newNudges.push({ id: `score-${Date.now()}`, type: "score", label: "Vivek · Arth Score", text: `Your Arth Score: ${scoreRaw.score}/100` });
      }
      if (schemes.length > 0) {
        setSchemeResults(schemes);
        setSchemesLoaded(true);
        newNudges.push({ id: `scheme-${Date.now()}`, type: "scheme", label: "Shilpi · Scheme Match", text: `${schemes.length} schemes matched for you` });
      }
      if (newNudges.length === 0) {
        newNudges.push({ id: `info-${Date.now()}`, type: "info", label: "ArthSetu", text: response.slice(0, 60) + (response.length > 60 ? "…" : "") });
      }

      setNudgeCards(prev => [...newNudges, ...prev].slice(0, 3));
      return entry;
    } catch {
      setOrbState("idle");
      const errEntry: HistoryEntry = {
        id: `${Date.now()}`,
        query: message,
        response: "Backend not reachable. Start FastAPI on port 8000.",
        intent: "error",
        scamDetected: false,
        schemes: [],
        score: null,
        timestamp: Date.now(),
      };
      setCurrentResponse(errEntry);
      setShowResponse(true);
      return errEntry;
    }
  }, [language, profile]);

  async function saveProfile() {
    const normalized = { ...profile, language };
    localStorage.setItem("arthsetu_profile", JSON.stringify(normalized));
    setProfile(normalized);
    setProfileReady(true);
    try {
      await fetch(`${API}/api/v1/profile/${normalized.user_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ updates: normalized }),
      });
    } catch {}
  }

  // ─── Voice Input ─────────────────────────────────────────────────────────────
  const startListening = useCallback(() => {
    if (orbState !== "idle") return;
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      setTranscript("Voice not supported. Use Chrome or Edge.");
      setShowResponse(false);
      return;
    }
    const r = new SR();
    r.lang = language === "hi" ? "hi-IN" : language === "en" ? "en-IN" : `${language}-IN`;
    r.interimResults = true;
    r.maxAlternatives = 1;
    r.onstart = () => { setOrbState("listening"); setTranscript(""); };
    r.onend = () => { setOrbState(current => current === "listening" ? "idle" : current); };
    r.onerror = () => { setOrbState("idle"); setTranscript("Couldn't hear clearly. Tap orb to try again."); };
    r.onresult = (e: any) => {
      const t = e.results[e.results.length - 1][0].transcript;
      setTranscript(t);
      if (e.results[e.results.length - 1].isFinal && t.trim()) {
        r.stop();
        setOrbState("thinking");
        callAPI(t.trim());
      }
    };
    r.start();
    recognitionRef.current = r;
  }, [orbState, language, callAPI]);

  // ─── Swipe Gesture Handling ──────────────────────────────────────────────────
  const THRESHOLD = 60;

  function handleSwipe(dx: number, dy: number) {
    if (activePanel !== "none") return;
    const adx = Math.abs(dx), ady = Math.abs(dy);
    if (Math.max(adx, ady) < THRESHOLD) return;

    if (ady > adx) {
      if (dy < 0) openPanel("score");   // swipe up → Account/Score
      else        openPanel("support"); // swipe down → Support
    } else {
      if (dx < 0) openPanel("history"); // swipe left → History
      else        openPanel("actions"); // swipe right → Smart Actions
    }
  }

  // Touch
  function onTouchStart(e: React.TouchEvent) {
    touchStart.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
  }
  function onTouchEnd(e: React.TouchEvent) {
    if (!touchStart.current) return;
    const dx = e.changedTouches[0].clientX - touchStart.current.x;
    const dy = e.changedTouches[0].clientY - touchStart.current.y;
    touchStart.current = null;
    handleSwipe(dx, dy);
  }
  // Mouse (desktop testing)
  function onMouseDown(e: React.MouseEvent) {
    mouseStart.current = { x: e.clientX, y: e.clientY };
  }
  function onMouseUp(e: React.MouseEvent) {
    if (!mouseStart.current) return;
    const dx = e.clientX - mouseStart.current.x;
    const dy = e.clientY - mouseStart.current.y;
    mouseStart.current = null;
    handleSwipe(dx, dy);
  }

  function openPanel(p: Panel) {
    setActivePanel(p);
    if (p === "score" && !scoreLoaded) loadScore();
  }
  function closePanel() { setActivePanel("none"); }

  // ─── Smart Actions ───────────────────────────────────────────────────────────
  async function loadScore() {
    if (scoreLoaded) return;
    setScoreLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/profile/${profile.user_id}`);
      if (res.ok) {
        const profile = await res.json();
        // Trigger a score query to actually compute the Arth Score
        const result = await callAPI("What is my Arth Score?", profile);
        if (result?.score) {
          setScoreData(result.score);
          setScoreLoaded(true);
        }
      }
    } finally {
      setScoreLoading(false);
    }
  }

  async function matchSchemes() {
    if (schemesLoaded) return;
    setSchemeLoading(true);
    try {
      const result = await callAPI("Which government schemes am I eligible for?");
      if (result?.schemes && result.schemes.length > 0) {
        setSchemeResults(result.schemes);
        setSchemesLoaded(true);
      } else {
        setSchemesLoaded(true); // even if 0, mark done
      }
    } finally {
      setSchemeLoading(false);
    }
  }

  async function runFraudCheck() {
    if (fraudCheckResult) return;
    setFraudLoading(true);
    try {
      // Ask user to speak or use last query
      const query = history[0]?.query || "Check for common financial scam patterns";
      const result = await callAPI(`Fraud check: ${query}`);
      setFraudCheckResult(result?.response || "No fraud indicators detected.");
    } finally {
      setFraudLoading(false);
    }
  }

  // ─── Nudge play ──────────────────────────────────────────────────────────────
  function playNudge(text: string) {
    speak(text, language);
  }

  function dismissNudge(id: string) {
    setNudgeCards(prev => prev.filter(n => n.id !== id));
  }

  // ─── Render ───────────────────────────────────────────────────────────────────
  if (!profileReady) {
    return (
      <div className="onboard-shell">
        <div className="onboard-card">
          <div className="app-name">ArthSetu</div>
          <h1>Set up your profile</h1>
          <p>Used for Arth Score, scheme matching, nudges, and personalized help.</p>
          <div className="onboard-grid">
            <label>Name<input value={profile.name} onChange={e => setProfile({ ...profile, name: e.target.value })} /></label>
            <label>Language<select value={language} onChange={e => setLanguage(e.target.value)}>{LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}</select></label>
            <label>Occupation<select value={profile.occupation} onChange={e => setProfile({ ...profile, occupation: e.target.value })}><option value="gig_worker">Gig worker</option><option value="farmer">Farmer</option><option value="daily_wage">Daily wage</option><option value="self_employed">Self employed</option><option value="salaried">Salaried</option><option value="street_vendor">Street vendor</option></select></label>
            <label>Age<input type="number" value={profile.age} onChange={e => setProfile({ ...profile, age: Number(e.target.value) })} /></label>
            <label>Monthly income<input type="number" value={profile.monthly_income_inr} onChange={e => setProfile({ ...profile, monthly_income_inr: Number(e.target.value) })} /></label>
            <label>Monthly expenses<input type="number" value={profile.monthly_expenses_inr} onChange={e => setProfile({ ...profile, monthly_expenses_inr: Number(e.target.value) })} /></label>
            <label>Emergency fund<input type="number" value={profile.emergency_fund_inr} onChange={e => setProfile({ ...profile, emergency_fund_inr: Number(e.target.value) })} /></label>
            <label>Monthly EMI<input type="number" value={profile.monthly_debt_emi_inr} onChange={e => setProfile({ ...profile, monthly_debt_emi_inr: Number(e.target.value) })} /></label>
          </div>
          <div className="check-grid">
            <label><input type="checkbox" checked={profile.has_bank_account} onChange={e => setProfile({ ...profile, has_bank_account: e.target.checked })} /> Bank account</label>
            <label><input type="checkbox" checked={profile.land_ownership} onChange={e => setProfile({ ...profile, land_ownership: e.target.checked })} /> Land owner</label>
            <label><input type="checkbox" checked={profile.has_disability} onChange={e => setProfile({ ...profile, has_disability: e.target.checked })} /> Disability support</label>
            <label><input type="checkbox" checked={profile.has_daughter_below_10} onChange={e => setProfile({ ...profile, has_daughter_below_10: e.target.checked })} /> Daughter below 10</label>
            <label><input type="checkbox" checked={profile.not_epf_member} onChange={e => setProfile({ ...profile, not_epf_member: e.target.checked })} /> Not EPF member</label>
          </div>
          <button className="onboard-btn" onClick={saveProfile}>Continue</button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="voice-shell"
      onTouchStart={onTouchStart}
      onTouchEnd={onTouchEnd}
      onMouseDown={onMouseDown}
      onMouseUp={onMouseUp}
    >
      {/* ── Status Bar ── */}
      <div className="status-bar">
        <div className="status-left">
          <div className={`status-icon ${isOnline ? "" : "offline"}`} />
          <span className="app-name">ArthSetu</span>
          {!isOnline && <span className="offline-badge">OFFLINE</span>}
        </div>
        <div className="status-right">
          <button
            className="mute-btn"
            onClick={() => {
              const next = !isMuted;
              setIsMuted(next);
              _isMuted = next;
              if (next) stopSpeaking();
            }}
            aria-label={isMuted ? "Unmute" : "Mute"}
            title={isMuted ? "Unmute" : "Mute"}
          >
            {isMuted ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <polygon points="11,5 6,9 2,9 2,15 6,15 11,19" fill="currentColor" />
                <line x1="23" y1="9" x2="17" y2="15" strokeLinecap="round" />
                <line x1="17" y1="9" x2="23" y2="15" strokeLinecap="round" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <polygon points="11,5 6,9 2,9 2,15 6,15 11,19" fill="currentColor" />
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07" strokeLinecap="round" />
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14" strokeLinecap="round" />
              </svg>
            )}
          </button>
          <span className="time-display">{timeStr}</span>
        </div>
      </div>

      {/* ── Swipe Hints (visible when no panel open) ── */}
      {activePanel === "none" && (
        <div className="swipe-hints">
          <button className="hint hint-up" onClick={() => openPanel("score")} aria-label="Open Arth Score">
            <svg className="hint-arrow hint-bounce-up" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M10 15V5M5 10l5-5 5 5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>Account</span>
          </button>
          <button className="hint hint-down" onClick={() => openPanel("support")} aria-label="Open support">
            <svg className="hint-arrow hint-bounce-down" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M10 5v10M15 10l-5 5-5-5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>Support</span>
          </button>
          <button className="hint hint-left" onClick={() => openPanel("history")} aria-label="Open history">
            <svg className="hint-arrow hint-bounce-left" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M15 10H5M10 5l-5 5 5 5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>History</span>
          </button>
          <button className="hint hint-right" onClick={() => openPanel("actions")} aria-label="Open smart actions">
            <svg className="hint-arrow hint-bounce-right" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M5 10h10M10 15l5-5-5-5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>Actions</span>
          </button>
        </div>
      )}

      {/* ── Orb ── */}
      {activePanel === "none" && (
        <div className="orb-zone">
          <div className="orb-outer">
            <div className="orb-ring" />
            <div className="orb-ring" />
            <div className="orb-ring" />
            <button
              className={`orb-core ${orbState === "listening" ? "listening" : orbState === "thinking" ? "thinking" : ""}`}
              onClick={startListening}
              id="voice-orb"
              aria-label="Tap to speak to ArthSetu"
            >
              <canvas
                ref={canvasRef}
                className={`waveform-canvas ${orbState === "listening" ? "active" : ""}`}
                width={200}
                height={200}
              />
              <span className="orb-icon">
                {orbState === "thinking" ? (
                  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5">
                    <circle cx="12" cy="12" r="10" strokeDasharray="30 10" strokeLinecap="round">
                      <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite" />
                    </circle>
                  </svg>
                ) : orbState === "listening" ? (
                  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5">
                    <rect x="9" y="2" width="6" height="12" rx="3" />
                    <path d="M5 10a7 7 0 0 0 14 0" strokeLinecap="round" />
                    <line x1="12" y1="17" x2="12" y2="22" strokeLinecap="round" />
                  </svg>
                ) : (
                  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5">
                    <rect x="9" y="2" width="6" height="12" rx="3" />
                    <path d="M5 10a7 7 0 0 0 14 0" strokeLinecap="round" />
                    <line x1="12" y1="17" x2="12" y2="22" strokeLinecap="round" />
                  </svg>
                )}
              </span>
            </button>
          </div>

          <div className="orb-label">
            <div className="orb-status">
              {orbState === "idle" && "Tap to speak"}
              {orbState === "listening" && "Listening…"}
              {orbState === "thinking" && "Thinking…"}
            </div>
            <div className="orb-sub">
              {orbState === "idle" && "ArthSetu · Your financial guardian"}
              {orbState === "listening" && "Speak your question in " + (LANGUAGES.find(l => l.code === language)?.label || "Hindi")}
              {orbState === "thinking" && "Running agents · Prahari · Shilpi · Vivek"}
            </div>
          </div>
        </div>
      )}

      {/* ── Transcript Strip ── */}
      <div className={`transcript-strip ${transcript && activePanel === "none" ? "visible" : ""}`}>
        {transcript}
      </div>

      {/* ── Nudge Cards ── */}
      {activePanel === "none" && nudgeCards.length > 0 && (
        <div className="nudge-dock">
          {nudgeCards.map((n) => (
            <div key={n.id} className="nudge-card" onClick={() => playNudge(n.text)}>
              <div className={`nudge-icon ${n.type}`}>
                {n.type === "scam" && "⚠️"}
                {n.type === "score" && "📊"}
                {n.type === "scheme" && "🏛️"}
                {n.type === "info" && "💬"}
              </div>
              <div className="nudge-body">
                <div className="nudge-label">{n.label}</div>
                <div className="nudge-text">{n.text}</div>
              </div>
              <div className="nudge-waveform">
                <span /><span /><span /><span /><span /><span />
              </div>
              <button className="play-btn" onClick={(e) => { e.stopPropagation(); playNudge(n.text); }} aria-label="Play audio">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
                  <polygon points="5,3 19,12 5,21" />
                </svg>
              </button>
              <button
                className="play-btn"
                style={{ fontSize: 12, width: 24, height: 24, background: "rgba(255,255,255,0.04)" }}
                onClick={(e) => { e.stopPropagation(); dismissNudge(n.id); }}
                aria-label="Dismiss"
              >✕</button>
            </div>
          ))}
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────── */}
      {/* ── PANEL: Account Overview (Swipe Up) ── */}
      {/* ─────────────────────────────────────────────────────────── */}
      <div className={`slide-panel from-top ${activePanel === "score" ? "visible" : ""}`}>
        <div className="panel-bar">
          <span className="panel-title">Account Overview</span>
          <button className="close-btn" onClick={closePanel}>✕</button>
        </div>
        <div className="panel-content">
          {scoreLoading && (
            <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "40px 0", justifyContent: "center", color: "var(--text-dim)", fontSize: 14 }}>
              <div className="spinner" /> Computing your Arth Score…
            </div>
          )}
          {!scoreLoading && scoreLoaded && scoreData && (
            <>
              <ScoreRing score={scoreData.score} band={scoreData.band} />
              <div className="metric-grid">
                <div className="metric-card">
                  <div className="metric-label">Savings Rate</div>
                  <div className="metric-value">{scoreData.savings_rate !== undefined ? `${Math.round(scoreData.savings_rate * 100)}%` : "--"}</div>
                  <div className="metric-sub">of monthly income</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Debt Ratio</div>
                  <div className="metric-value">{scoreData.debt_ratio !== undefined ? `${Math.round(scoreData.debt_ratio * 100)}%` : "--"}</div>
                  <div className="metric-sub">of monthly income</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Band</div>
                  <div className="metric-value" style={{ fontSize: 16, textTransform: "capitalize" }}>{scoreData.band?.replace(/_/g, " ") || "--"}</div>
                  <div className="metric-sub">financial health</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Sessions</div>
                  <div className="metric-value">{history.length}</div>
                  <div className="metric-sub">conversations</div>
                </div>
              </div>
              {scoreData.next_best_action && (
                <div className="action-text">
                  <strong style={{ color: "var(--orange)", fontSize: 12, display: "block", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.5px" }}>Next Best Action</strong>
                  {scoreData.next_best_action}
                </div>
              )}
            </>
          )}
          {!scoreLoading && !scoreLoaded && (
            <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--text-faint)", fontSize: 14 }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>📊</div>
              <div style={{ marginBottom: 8, fontWeight: 600, color: "var(--text-dim)" }}>Arth Score not yet computed</div>
              <div>Speak a query to the orb and your score will appear here.</div>
            </div>
          )}
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────── */}
      {/* ── PANEL: Payment History (Swipe Left) ── */}
      {/* ─────────────────────────────────────────────────────────── */}
      <div className={`slide-panel from-left ${activePanel === "history" ? "visible" : ""}`}>
        <div className="panel-bar">
          <span className="panel-title">Conversation History</span>
          <button className="close-btn" onClick={closePanel}>✕</button>
        </div>
        <div className="panel-content">
          {history.length === 0 ? (
            <div className="empty-history">
              <div style={{ fontSize: 40, marginBottom: 12 }}>🎙️</div>
              <div style={{ fontWeight: 600, color: "var(--text-dim)", marginBottom: 6 }}>No conversations yet</div>
              <div>Tap the orb and speak your first question.</div>
            </div>
          ) : (
            <div className="history-list">
              {history.map(h => (
                <div key={h.id} className="history-item" onClick={() => {
                  setCurrentResponse(h);
                  setShowResponse(true);
                  closePanel();
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <div className="history-intent">{h.intent}</div>
                    <span className={`risk-badge ${h.scamDetected ? "risk-high" : "risk-clear"}`}>
                      {h.scamDetected ? "⚠ SCAM" : "✓ CLEAR"}
                    </span>
                  </div>
                  <div className="history-query">"{h.query}"</div>
                  <div className="history-response">{h.response}</div>
                  <div className="history-meta">
                    <span>{formatTime(h.timestamp)}</span>
                    {h.schemes.length > 0 && <span>· {h.schemes.length} schemes</span>}
                    {h.score && <span>· Score: {h.score.score}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────── */}
      {/* ── PANEL: Smart Actions (Swipe Right) ── */}
      {/* ─────────────────────────────────────────────────────────── */}
      <div className={`slide-panel from-right ${activePanel === "actions" ? "visible" : ""}`}>
        <div className="panel-bar">
          <span className="panel-title">Smart Actions</span>
          <button className="close-btn" onClick={closePanel}>✕</button>
        </div>

        {/* Mesh / NFC section */}
        <div className="mesh-badge">
          <span>⬡</span>
          <span>{isOnline ? "Online · All agents active" : "Offline Mode · Cached data only"}</span>
        </div>
        <div className="nfc-stripe">
          <span className="nfc-icon">📲</span>
          <div className="nfc-text">
            <div className="nfc-title">UPI Lite X · Offline payments</div>
            <div className="nfc-sub">Tap NFC to settle offline via UPI Lite</div>
          </div>
          <span className="nfc-lock">{isOnline ? "ONLINE" : "OFFLINE"}</span>
        </div>

        <div className="actions-grid">
          {/* Scheme Matcher */}
          <div
            id="action-scheme-match"
            className={`action-card ${schemeLoading ? "loading" : ""}`}
            onClick={async () => {
              if (!schemesLoaded) await matchSchemes();
            }}
          >
            <div className="action-icon-wrap green">🏛️</div>
            <div className="action-info">
              <div className="action-title">Match Government Schemes</div>
              <div className="action-desc">Find PM-Kisan, Atal Pension, PMJDY, and more that fit your profile</div>
            </div>
            {schemeLoading ? <div className="spinner" /> : (
              <svg className="action-chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18l6-6-6-6" /></svg>
            )}
          </div>

          {/* Show scheme results inline */}
          {schemesLoaded && (
            <div className="scheme-results" style={{ padding: "0 0 4px" }}>
              {schemeResults.length === 0 ? (
                <div className="no-schemes">No schemes matched for current profile. Speak a profile query to the orb first.</div>
              ) : (
                schemeResults.map((s, i) => (
                  <div key={i} className="scheme-card">
                    <div className="scheme-name">{s.name}</div>
                    {s.description && <div className="scheme-desc">{s.description}</div>}
                    {s.eligibility && <div className="scheme-desc" style={{ marginTop: 4, fontStyle: "italic" }}>{s.eligibility}</div>}
                    {s.tags && s.tags.length > 0 && (
                      <div className="scheme-tags">
                        {s.tags.map((t, j) => <span key={j} className="scheme-tag">{t}</span>)}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Fraud / Scam Check */}
          <div
            id="action-fraud-check"
            className={`action-card ${fraudLoading ? "loading" : ""}`}
            onClick={runFraudCheck}
          >
            <div className="action-icon-wrap red">🛡️</div>
            <div className="action-info">
              <div className="action-title">Prahari Fraud Check</div>
              <div className="action-desc">Run scam detection on your last message or speak a suspicious one</div>
            </div>
            {fraudLoading ? <div className="spinner" /> : (
              <svg className="action-chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18l6-6-6-6" /></svg>
            )}
          </div>

          {fraudCheckResult && (
            <div className="action-text" style={{ margin: "0 0 4px" }}>{fraudCheckResult}</div>
          )}

          {/* Arth Score */}
          <div
            id="action-arth-score"
            className={`action-card ${scoreLoading ? "loading" : ""}`}
            onClick={() => { openPanel("score"); }}
          >
            <div className="action-icon-wrap blue">📊</div>
            <div className="action-info">
              <div className="action-title">View Arth Score</div>
              <div className="action-desc">Your financial health index — savings, debt, behaviour</div>
            </div>
            <svg className="action-chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18l6-6-6-6" /></svg>
          </div>

          {/* Budget Planner */}
          <div
            id="action-budget"
            className="action-card"
            onClick={() => {
              closePanel();
              callAPI("Plan my monthly budget. My income is Rs 20000 and expenses are around Rs 14000.");
            }}
          >
            <div className="action-icon-wrap orange">💰</div>
            <div className="action-info">
              <div className="action-title">Shilpi Budget Planner</div>
              <div className="action-desc">Monthly rupee plan — savings, EMI, emergency fund</div>
            </div>
            <svg className="action-chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18l6-6-6-6" /></svg>
          </div>

          {/* Paisa Padhai */}
          <div
            id="action-learn"
            className="action-card"
            onClick={() => {
              closePanel();
              callAPI("Explain what APR means and why it matters for loans in simple Hindi.");
            }}
          >
            <div className="action-icon-wrap purple">🎓</div>
            <div className="action-info">
              <div className="action-title">Paisa Padhai</div>
              <div className="action-desc">Learn financial basics — APR, EMI, CIBIL, UPI explained simply</div>
            </div>
            <svg className="action-chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18l6-6-6-6" /></svg>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────── */}
      {/* ── PANEL: Support (Swipe Down) ── */}
      {/* ─────────────────────────────────────────────────────────── */}
      <div className={`slide-panel from-bottom ${activePanel === "support" ? "visible" : ""}`}>
        <div className="panel-bar">
          <span className="panel-title">Support & Settings</span>
          <button className="close-btn" onClick={closePanel}>✕</button>
        </div>
        <div className="panel-content" style={{ padding: 0 }}>

          {/* Language Selector */}
          <div style={{ padding: "16px 20px 8px" }}>
            <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-faint)", marginBottom: 10 }}>
              Response Language
            </div>
            <div className="lang-grid">
              {LANGUAGES.map(l => (
                <button
                  key={l.code}
                  id={`lang-${l.code}`}
                  className={`lang-btn ${language === l.code ? "active" : ""}`}
                  onClick={() => setLanguage(l.code)}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>

          <div className="support-list">
            <div className="support-item" onClick={() => { closePanel(); callAPI("Help me. I think I am being scammed right now. Someone is asking for my OTP."); }}>
              <span className="support-icon">🚨</span>
              <div>
                <div className="support-label">Emergency Scam Alert</div>
                <div className="support-desc">Immediate fraud help — Prahari activates instantly</div>
              </div>
            </div>
            <div className="support-item" onClick={() => { closePanel(); callAPI("I want to report a financial fraud to RBI Sachet. Help me file a complaint."); }}>
              <span className="support-icon">📋</span>
              <div>
                <div className="support-label">Report to RBI Sachet</div>
                <div className="support-desc">File a fraud complaint with regulatory body</div>
              </div>
            </div>
            <div className="support-item" onClick={() => { closePanel(); callAPI("I am a farmer and need help with PM-Kisan and crop insurance schemes."); }}>
              <span className="support-icon">🌾</span>
              <div>
                <div className="support-label">Kisan Support</div>
                <div className="support-desc">PM-Kisan, crop insurance, PMFBY — farmer-specific help</div>
              </div>
            </div>
            <div className="support-item" onClick={() => {
              const text = currentResponse?.response || "ArthSetu is your AI financial guardian. Tap the orb and speak.";
              speak(text, language);
            }}>
              <span className="support-icon">🔊</span>
              <div>
                <div className="support-label">Replay Last Response</div>
                <div className="support-desc">Hear the last ArthSetu answer again</div>
              </div>
            </div>
            <div className="support-item" onClick={() => {
              setHistory([]);
              setNudgeCards([]);
              setSchemeResults([]);
              setSchemesLoaded(false);
              setFraudCheckResult(null);
              setScoreData(null);
              setScoreLoaded(false);
              closePanel();
            }}>
              <span className="support-icon">🔄</span>
              <div>
                <div className="support-label">Clear Session</div>
                <div className="support-desc">Reset conversation and cached results</div>
              </div>
            </div>
          </div>

          <div style={{ padding: "16px 20px" }}>
            <div style={{ fontSize: 11, color: "var(--text-faint)", lineHeight: 1.6, textAlign: "center" }}>
              ArthSetu · Paisa Samajho, Zindagi Badlo<br />
              Powered by Sutradhar · Prahari · Bodhak · Shilpi · Vivek
            </div>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────── */}
      {/* ── Response Bottom Sheet ── */}
      {/* ─────────────────────────────────────────────────────────── */}
      <div className={`response-overlay ${showResponse && activePanel === "none" ? "visible" : ""}`}>
        <div className="response-sheet">
          <div className="sheet-handle" />
          {currentResponse && (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                <div className="sheet-intent">{currentResponse.intent}</div>
                <span className={`risk-badge ${currentResponse.scamDetected ? "risk-high" : "risk-clear"}`}>
                  {currentResponse.scamDetected ? "⚠ SCAM DETECTED" : "✓ Prahari Clear"}
                </span>
              </div>
              <div style={{ fontSize: 13, color: "var(--text-faint)", marginBottom: 10, fontStyle: "italic" }}>
                "{currentResponse.query}"
              </div>
              <div className="sheet-response">{currentResponse.response}</div>
              <div className="sheet-actions">
                <button className="sheet-btn primary" onClick={() => speak(currentResponse.response, language)}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="11,5 6,9 2,9 2,15 6,15 11,19" fill="white" /><path d="M15.54 8.46a5 5 0 0 1 0 7.07" /><path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                  </svg>
                  Play
                </button>
                <button className="sheet-btn" onClick={() => { setShowResponse(false); setTranscript(""); }}>
                  Dismiss
                </button>
                <button className="sheet-btn" onClick={() => { setShowResponse(false); startListening(); }}>
                  Ask Again
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
