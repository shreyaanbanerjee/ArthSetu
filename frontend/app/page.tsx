"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { 
  ShieldCheck, 
  ShieldAlert, 
  Mic, 
  MicOff, 
  Send, 
  Volume2, 
  VolumeX, 
  User, 
  HelpCircle, 
  ExternalLink, 
  PhoneCall, 
  FileText, 
  Award, 
  Clock, 
  CheckCircle2, 
  AlertTriangle,
  BookOpen
} from "lucide-react";

// Types
type TabType = "assistant" | "schemes" | "score" | "fraud" | "history" | "guide";

interface ArthScore {
  score: number;
  band: string;
  next_best_action?: string;
  savings_rate?: number;
  debt_ratio?: number;
}

interface SchemeItem {
  name: string;
  description?: string;
  benefit?: string;
  eligibility?: string;
  tags?: string[];
  apply_url?: string;
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

function getApiFallbacks(): string[] {
  const list: string[] = [];
  if (typeof window !== "undefined" && window.location?.origin) {
    list.push(window.location.origin);
  }
  const envApi = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envApi && !envApi.includes("localhost")) {
    list.push(envApi);
  }
  list.push("http://localhost:8000");
  list.push("http://127.0.0.1:8000");
  return Array.from(new Set(list.filter(Boolean)));
}

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

const PRESET_SCHEMES: SchemeItem[] = [
  {
    name: "PM SVANidhi (पीएम स्वनिधि)",
    benefit: "₹10,000 से ₹50,000 तक ब्याज-सब्सिडी ऋण",
    eligibility: "शहरी एवं अर्ध-शहरी क्षेत्रों के रेहड़ी-पटरी विक्रेता व स्ट्रीट वेंडर्स",
    description: "बिना किसी गारंटी के कार्यशील पूंजी ऋण, समय पर भुगतान करने पर 7% ब्याज सब्सिडी और डिजिटल लेनदेन पर कैशबैक।",
    apply_url: "https://pmsvanidhi.mohua.gov.in/",
  },
  {
    name: "PM Suraksha Bima Yojana (PMSBY)",
    benefit: "₹2 लाख का दुर्घटना बीमा মাত্র ₹20 प्रति वर्ष",
    eligibility: "18 से 70 वर्ष आयु के सभी बैंक खाताधारक",
    description: "आकस्मिक मृत्यु या पूर्ण दिव्यांगता की स्थिति में ₹2,00,000 की वित्तीय सुरक्षा सीधे बैंक खाते से ऑटो-डेबिट।",
    apply_url: "https://www.jansuraksha.gov.in/",
  },
  {
    name: "PM Jeevan Jyoti Bima Yojana (PMJJBY)",
    benefit: "₹2 लाख का जीवन बीमा मात्र ₹436 प्रति वर्ष",
    eligibility: "18 से 50 वर्ष आयु के बचत बैंक खाताधारक",
    description: "किसी भी कारण से मृत्यु होने पर परिवार को ₹2,00,000 की एकमुश्त जीवन सुरक्षा सहायता।",
    apply_url: "https://www.jansuraksha.gov.in/",
  },
  {
    name: "Pradhan Mantri Mudra Yojana (PMMY)",
    benefit: "₹50,000 तक शिशु ऋण (बिना गारंटी)",
    eligibility: "छोटे व्यापारी, कारीगर, फल-सब्जी विक्रेता, सेवा प्रदाता",
    description: "सूक्ष्म एवं लघु व्यापार शुरू करने या बढ़ाने के लिए बैंकों और NBFCs से आसान ऋण सुविधा।",
    apply_url: "https://www.mudra.org.in/",
  },
  {
    name: "Sukanya Samriddhi Yojana (SSY)",
    benefit: "8.2% ब्याज दर + 100% कर छूट",
    eligibility: "10 वर्ष से कम आयु की बालिकाओं के अभिभावक",
    description: "बालिका की उच्च शिक्षा एवं विवाह के लिए डाकघर या अधिकृत बैंक में खोला जाने वाला विशेष बचत खाता।",
    apply_url: "https://www.indiapost.gov.in/",
  },
  {
    name: "Atal Pension Yojana (APY)",
    benefit: "₹1,000 से ₹5,000 मासिक आजीवन पेंशन",
    eligibility: "18 से 40 वर्ष के असंगठित क्षेत्र के श्रमिक",
    description: "60 वर्ष की आयु के बाद भारत सरकार द्वारा गारंटीकृत मासिक पेंशन का सामाजिक सुरक्षा कवच।",
    apply_url: "https://www.npscra.nsdl.co.in/",
  },
];

let _isMuted = false;

function stopSpeaking() {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

function speak(text: string, lang: string) {
  if (_isMuted || typeof window === "undefined" || !("speechSynthesis" in window)) return;
  const clean = text.replace(/[*#_`]/g, "");

  const langMap: Record<string, string> = {
    hi: "hi-IN", en: "en-IN", mr: "mr-IN", kn: "kn-IN",
    ta: "ta-IN", te: "te-IN", bn: "bn-IN", gu: "gu-IN", pa: "pa-IN",
  };
  const targetLang = langMap[lang] || "hi-IN";

  const run = () => {
    window.speechSynthesis.cancel();
    window.speechSynthesis.resume();
    const utt = new SpeechSynthesisUtterance(clean);
    utt.lang = targetLang;
    utt.rate = 0.95;

    const voices = window.speechSynthesis.getVoices();
    let match = voices.find(v => v.lang.toLowerCase().startsWith(targetLang.toLowerCase().split("-")[0]));
    if (!match && (lang === "mr" || lang === "hi" || lang === "gu" || lang === "bn")) {
      match = voices.find(v => v.lang.toLowerCase().startsWith("hi"));
      if (match) utt.lang = "hi-IN";
    }
    if (match) utt.voice = match;
    window.speechSynthesis.speak(utt);
  };

  if (window.speechSynthesis.getVoices().length === 0) {
    const onVoicesChanged = () => {
      window.speechSynthesis.removeEventListener("voiceschanged", onVoicesChanged);
      run();
    };
    window.speechSynthesis.addEventListener("voiceschanged", onVoicesChanged);
    setTimeout(() => {
      window.speechSynthesis.removeEventListener("voiceschanged", onVoicesChanged);
      run();
    }, 500);
  } else {
    run();
  }
}

export default function ArthSetuApp() {
  const [activeTab, setActiveTab] = useState<TabType>("assistant");
  const [isOnline, setIsOnline] = useState(true);
  const [isMuted, setIsMutedState] = useState(false);
  const [inputText, setInputText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);

  // User Profile
  const [profile, setProfile] = useState<UserProfile>({
    user_id: "demo-user",
    name: "रामेश्वर कुमार",
    language: "hi",
    occupation: "स्ट्रीट वेंडर (फल विक्रेता)",
    age: 34,
    monthly_income_inr: 16000,
    monthly_expenses_inr: 11000,
    emergency_fund_inr: 6000,
    monthly_debt_emi_inr: 2500,
    has_bank_account: true,
    has_disability: false,
    land_ownership: false,
    has_daughter_below_10: true,
    not_epf_member: true,
  });

  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [arthScore, setArthScore] = useState<ArthScore>({
    score: 64,
    band: "improving",
    next_best_action: "पीएम सुरक्षा बीमा योजना (₹20/वर्ष) लेकर आकस्मिक सुरक्षा मजबूत करें।",
    savings_rate: 31.2,
    debt_ratio: 15.6,
  });

  const recognitionRef = useRef<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Synchronize mute state
  const toggleMute = () => {
    _isMuted = !_isMuted;
    setIsMutedState(_isMuted);
    if (_isMuted) stopSpeaking();
  };

  // Online / Offline listener with clean unmount cleanup
  useEffect(() => {
    setIsOnline(navigator.onLine);
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  // Load profile from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem("arthsetu_profile_v2");
      if (saved) {
        setProfile(JSON.parse(saved));
      }
    } catch {
      // Ignore storage errors
    }
  }, []);

  // Scroll to bottom of chat on new messages
  useEffect(() => {
    if (activeTab === "assistant") {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [history, isThinking, activeTab]);

  // Execute API Request
  const sendMessage = useCallback(async (msg: string) => {
    const textToSend = msg.trim();
    if (!textToSend || isThinking) return;

    setIsThinking(true);
    setInputText("");

    const userMessageEntry: HistoryEntry = {
      id: `u-${Date.now()}`,
      query: textToSend,
      response: "",
      intent: "query",
      scamDetected: false,
      schemes: [],
      score: null,
      timestamp: Date.now(),
    };

    // Optimistically append user message
    setHistory(prev => [...prev, userMessageEntry]);

    try {
      let res: Response | null = null;
      const payload = {
        user_id: profile.user_id,
        message: textToSend,
        language: profile.language,
        profile_updates: profile,
      };

      const fallbacks = getApiFallbacks();
      for (const baseUrl of fallbacks) {
        try {
          res = await fetch(`${baseUrl}/api/v1/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          if (res.ok) break;
        } catch {
          res = null;
        }
      }

      if (!res || !res.ok) {
        throw new Error("Service unavailable");
      }

      const data = await res.json();
      const responseText = data.final_response || "अनुरोध प्रोसेस हो गया है।";
      const scamDetected = Boolean(data.scam_detected);
      const matchedSchemes: SchemeItem[] = data.scheme_matches || data.agent_outputs?.shilpi?.schemes_to_apply || [];
      const updatedScore = data.arth_score_update || data.agent_outputs?.vivek?.arth_score || null;

      if (updatedScore && typeof updatedScore.score === "number") {
        setArthScore(updatedScore);
      }

      const assistantEntry: HistoryEntry = {
        id: `a-${Date.now()}`,
        query: textToSend,
        response: responseText,
        intent: data.intent || "general",
        scamDetected,
        schemes: matchedSchemes,
        score: updatedScore,
        timestamp: Date.now(),
      };

      setHistory(prev => [...prev.slice(0, prev.length - 1), { ...userMessageEntry, response: responseText, scamDetected, schemes: matchedSchemes, score: updatedScore }]);
      speak(responseText, profile.language);
    } catch {
      const fallbackEntry: HistoryEntry = {
        ...userMessageEntry,
        response: "सर्वर से संपर्क नहीं हो पाया। कृपया सुनिश्चित करें कि बैकएंड सेवा (पोर्ट 8000) चालू है।",
        intent: "error",
      };
      setHistory(prev => [...prev.slice(0, prev.length - 1), fallbackEntry]);
    } finally {
      setIsThinking(false);
    }
  }, [profile, isThinking]);

  // Voice Recognition Handler
  const toggleListening = () => {
    if (isRecording) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsRecording(false);
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("आपके ब्राउज़र में वॉइस इनपुट समर्थित नहीं है। कृपया टेक्स्ट का उपयोग करें।");
      return;
    }

    try {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = true;

      const langMap: Record<string, string> = {
        hi: "hi-IN", en: "en-IN", mr: "mr-IN", kn: "kn-IN",
        ta: "ta-IN", te: "te-IN", bn: "bn-IN", gu: "gu-IN", pa: "pa-IN",
      };
      rec.lang = langMap[profile.language] || "hi-IN";

      rec.onstart = () => {
        setIsRecording(true);
      };

      rec.onresult = (e: any) => {
        const transcript = Array.from(e.results)
          .map((res: any) => res[0].transcript)
          .join("");
        setInputText(transcript);
        if (e.results[0].isFinal) {
          rec.stop();
          setIsRecording(false);
          sendMessage(transcript);
        }
      };

      rec.onerror = () => {
        setIsRecording(false);
      };

      rec.onend = () => {
        setIsRecording(false);
      };

      rec.start();
      recognitionRef.current = rec;
    } catch (err) {
      console.error("Speech recognition error:", err);
      setIsRecording(false);
    }
  };

  const handleProfileSave = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      localStorage.setItem("arthsetu_profile_v2", JSON.stringify(profile));
    } catch {
      // Storage unavailable
    }
    setShowProfileModal(false);
  };

  const handleTryScenario = (promptText: string) => {
    setActiveTab("assistant");
    setTimeout(() => {
      sendMessage(promptText);
    }, 50);
  };

  return (
    <div className="app-shell">
      {/* Top Government/Fintech Navigation Bar */}
      <header className="gov-header">
        <div className="gov-header-inner">
          <div className="brand-section">
            <div className="brand-emblem" aria-hidden="true">₹</div>
            <div className="brand-titles">
              <h1>अर्थसेतु (ArthSetu)</h1>
              <div className="brand-sub">जन वित्तीय सुरक्षा एवं सशक्तिकरण</div>
            </div>
          </div>

          <div className="header-controls">
            <select 
              className="lang-select"
              value={profile.language}
              onChange={(e) => setProfile(p => ({ ...p, language: e.target.value }))}
              aria-label="भाषा चुनें"
            >
              {LANGUAGES.map(l => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </select>

            <button 
              className="profile-chip-btn" 
              onClick={() => setShowProfileModal(true)}
              title="प्रोफाइल संपादित करें"
            >
              <User size={14} />
              <span>{profile.name.split(" ")[0]}</span>
            </button>

            <button 
              className="icon-btn" 
              onClick={toggleMute}
              title={isMuted ? "ध्वनि चालू करें" : "ध्वनि म्यूट करें"}
              aria-label="ध्वनि टॉगल"
            >
              {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
            </button>

            <div className="status-indicator">
              <div className="status-dot" style={{ backgroundColor: isOnline ? "#34d399" : "#ef4444" }} />
              <span>{isOnline ? "ऑनलाइन" : "ऑफलाइन"}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Primary Tab Navigation */}
      <nav className="tabs-nav" aria-label="मुख्य अनुभाग">
        <button 
          className={`tab-btn ${activeTab === "assistant" ? "active" : ""}`}
          onClick={() => setActiveTab("assistant")}
        >
          <HelpCircle size={16} />
          <span>संवाद सहायक</span>
        </button>

        <button 
          className={`tab-btn ${activeTab === "schemes" ? "active" : ""}`}
          onClick={() => setActiveTab("schemes")}
        >
          <FileText size={16} />
          <span>सरकारी योजनाएं</span>
        </button>

        <button 
          className={`tab-btn ${activeTab === "score" ? "active" : ""}`}
          onClick={() => setActiveTab("score")}
        >
          <Award size={16} />
          <span>अर्थ स्कोर</span>
        </button>

        <button 
          className={`tab-btn ${activeTab === "fraud" ? "active" : ""}`}
          onClick={() => setActiveTab("fraud")}
        >
          <ShieldAlert size={16} />
          <span>सुरक्षा कवच</span>
        </button>

        <button 
          className={`tab-btn ${activeTab === "history" ? "active" : ""}`}
          onClick={() => setActiveTab("history")}
        >
          <Clock size={16} />
          <span>इतिहास</span>
        </button>

        <button 
          className={`tab-btn ${activeTab === "guide" ? "active" : ""}`}
          onClick={() => setActiveTab("guide")}
        >
          <BookOpen size={16} />
          <span>मार्गदर्शिका (Guide)</span>
        </button>
      </nav>

      {/* Main Tab Views */}
      <main className="tab-content-area">
        {/* TAB 1: ASSISTANT */}
        {activeTab === "assistant" && (
          <div className="chat-container">
            <div className="chat-messages">
              {history.length === 0 && (
                <div className="welcome-hero">
                  <h2>नमस्ते, {profile.name}!</h2>
                  <p>
                    मैं आपका अर्थसेतु वित्तीय सहायक हूँ। आप सरकारी योजनाओं की जानकारी, 
                    लोन व ब्याज दरों की सुरक्षा जांच, या अपनी बचत क्षमता के बारे में 
                    बोलकर या लिखकर पूछ सकते हैं।
                  </p>

                  <div className="quick-prompts-title">सुझाए गए प्रश्न (टैप करें)</div>
                  <div className="quick-prompts-grid">
                    <button 
                      className="quick-prompt-btn"
                      onClick={() => sendMessage("क्या मुझे पीएम स्वनिधि ₹10,000 लोन मिल सकता है?")}
                    >
                      💡 क्या मुझे पीएम स्वनिधि योजना में लोन मिल सकता है?
                    </button>
                    <button 
                      className="quick-prompt-btn"
                      onClick={() => sendMessage("मुझे मैसेज आया है कि ₹500 प्रोसेसिंग फीस देने पर तुरंत ₹50,000 लोन मिल जाएगा, क्या यह सही है?")}
                    >
                      🔍 '₹500 फीस देकर ₹50,000 लोन पाएं' — क्या यह सच है?
                    </button>
                    <button 
                      className="quick-prompt-btn"
                      onClick={() => sendMessage("मेरा अर्थ स्कोर कितना है और मैं अपनी बचत कैसे बढ़ा सकता हूँ?")}
                    >
                      📊 मेरा अर्थ स्कोर और बचत क्षमता कितनी है?
                    </button>
                    <button 
                      className="quick-prompt-btn"
                      onClick={() => sendMessage("बिजली कनेक्शन कटने का मैसेज और APK फाइल डाउनलोड करने को कहा गया है, क्या करूं?")}
                    >
                      ⚠️ बिजली बिल कटने का मैसेज आया है, क्या करूं?
                    </button>
                  </div>
                </div>
              )}

              {history.map((item) => (
                <div key={item.id} className="message-group" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  {/* User Query */}
                  <div className="message-row user">
                    <div className="bubble-user">
                      {item.query}
                      <span className="timestamp" style={{ color: "#cbd5e1" }}>
                        {new Date(item.timestamp).toLocaleTimeString("hi-IN", { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                  </div>

                  {/* Assistant Response */}
                  {item.response && (
                    <div className="message-row assistant">
                      <div className="bubble-assistant">
                        <div className="assistant-meta">
                          {item.scamDetected ? (
                            <span className="security-badge threat">
                              <ShieldAlert size={14} />
                              <span>सुरक्षा चेतावनी: धोखाधड़ी संकेत</span>
                            </span>
                          ) : (
                            <span className="security-badge safe">
                              <ShieldCheck size={14} />
                              <span>प्रहरी सत्यापित: सुरक्षित परामर्श</span>
                            </span>
                          )}

                          <button 
                            className="audio-replay-btn"
                            onClick={() => speak(item.response, profile.language)}
                            title="पुनः सुनें"
                          >
                            <Volume2 size={13} />
                            <span>सुनें</span>
                          </button>
                        </div>

                        <div className="assistant-body">
                          {item.response}
                        </div>

                        {item.schemes && item.schemes.length > 0 && (
                          <div style={{ marginTop: "12px", paddingTop: "10px", borderTop: "1px solid #e2e8f0" }}>
                            <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--gov-navy)", marginBottom: "6px" }}>
                              संबंधित सरकारी योजनाएं:
                            </div>
                            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                              {item.schemes.slice(0, 2).map((s, idx) => (
                                <div key={idx} style={{ padding: "8px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0", fontSize: "12px" }}>
                                  <strong>{s.name}</strong> — {s.benefit || s.description}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        <span className="timestamp">
                          {new Date(item.timestamp).toLocaleTimeString("hi-IN", { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {isThinking && (
                <div className="message-row assistant">
                  <div className="bubble-assistant" style={{ fontStyle: "italic", color: "var(--text-muted)" }}>
                    अर्थसेतु विश्लेषण कर रहा है...
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Sticky Input Bar */}
            <div className="chat-input-bar">
              {isRecording && (
                <div className="recording-indicator">
                  <div className="recording-pulse">
                    <div className="pulse-dot" />
                    <span>सुन रहा हूँ... स्पष्ट आवाज़ में बोलें (रोकने के लिए पुनः टैप करें)</span>
                  </div>
                  <button 
                    onClick={toggleListening}
                    style={{ background: "none", border: "none", color: "var(--color-danger)", fontWeight: 700, cursor: "pointer" }}
                  >
                    रोकें
                  </button>
                </div>
              )}

              <form 
                className="input-controls-row" 
                onSubmit={(e) => { e.preventDefault(); sendMessage(inputText); }}
              >
                <input 
                  type="text" 
                  className="chat-input-field"
                  placeholder="अपना सवाल यहाँ लिखें या माइक पर टैप करें..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  disabled={isThinking}
                />

                <button 
                  type="button"
                  className={`mic-toggle-btn ${isRecording ? "recording" : ""}`}
                  onClick={toggleListening}
                  title={isRecording ? "रिकॉर्डिंग रोकें" : "बोलकर पूछें"}
                >
                  {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
                </button>

                <button 
                  type="submit" 
                  className="send-action-btn"
                  disabled={!inputText.trim() || isThinking}
                  title="भेजें"
                >
                  <Send size={18} />
                </button>
              </form>
            </div>
          </div>
        )}

        {/* TAB 2: SCHEMES */}
        {activeTab === "schemes" && (
          <div>
            <div className="panel-header-block">
              <div className="panel-title">कल्याणकारी सरकारी योजनाएं (Welfare Schemes)</div>
              <div className="panel-description">
                आपकी आय, व्यवसाय और पारिवारिक स्थिति के आधार पर सत्यापित सरकारी वित्तीय योजनाएं।
              </div>
            </div>

            <div className="cards-grid-view">
              {PRESET_SCHEMES.map((scheme, idx) => (
                <div key={idx} className="info-card">
                  <div className="info-card-header">
                    <div className="info-card-title">{scheme.name}</div>
                    <span className="benefit-pill">{scheme.benefit}</span>
                  </div>

                  <div className="info-card-body">
                    <p style={{ marginBottom: "8px" }}>{scheme.description}</p>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                      <strong>पात्रता:</strong> {scheme.eligibility}
                    </div>
                  </div>

                  {scheme.apply_url && (
                    <a 
                      href={scheme.apply_url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="card-action-link"
                    >
                      <span>आधिकारिक पोर्टल पर आवेदन करें</span>
                      <ExternalLink size={13} />
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: ARTH SCORE */}
        {activeTab === "score" && (
          <div className="score-dashboard">
            <div className="panel-header-block" style={{ borderRadius: "12px", border: "1px solid var(--border-light)" }}>
              <div className="panel-title">अर्थ स्कोर एवं वित्तीय स्वास्थ्य (Arth Score)</div>
              <div className="panel-description">
                अनौपचारिक श्रमिकों एवं छोटे उद्यमियों के लिए 5 मापदंडों पर आधारित वित्तीय मजबूती सूचकांक।
              </div>
            </div>

            <div className="score-hero-card">
              <div className="score-visual-gauge">
                <svg className="score-svg-circle" width="140" height="140" viewBox="0 0 140 140">
                  <circle className="score-gauge-track" cx="70" cy="70" r="54" />
                  <circle 
                    className="score-gauge-value" 
                    cx="70" 
                    cy="70" 
                    r="54"
                    stroke={arthScore.score >= 60 ? "#059669" : arthScore.score >= 40 ? "#f97316" : "#dc2626"}
                    strokeDasharray={339.29}
                    strokeDashoffset={339.29 * (1 - arthScore.score / 100)}
                  />
                </svg>
                <div className="score-gauge-number">
                  <span className="val">{arthScore.score}</span>
                  <span className="den">/ 100</span>
                </div>
              </div>

              <div className="score-meta-block">
                <h3>वित्तीय स्थिति: {arthScore.score >= 70 ? "स्थिर (Stable)" : arthScore.score >= 50 ? "सुधारशील (Improving)" : "संवेदनशील (Fragile)"}</h3>
                <span className={`score-band-tag band-${arthScore.band}`}>
                  स्थिति श्रेणी: {arthScore.band}
                </span>
                <p style={{ fontSize: "13px", color: "var(--text-muted)", lineHeight: 1.5 }}>
                  {arthScore.next_best_action || "ऋण अनुपात कम रखने और आपातकालीन बचत बढ़ाने से आपका स्कोर और सुधरेगा।"}
                </p>
              </div>
            </div>

            <div className="pillars-grid">
              <div className="pillar-box">
                <div className="label">मासिक आय (Income)</div>
                <div className="value">₹{profile.monthly_income_inr.toLocaleString("en-IN")}</div>
              </div>

              <div className="pillar-box">
                <div className="label">ऋण ईएमआई (Monthly EMI)</div>
                <div className="value">₹{profile.monthly_debt_emi_inr.toLocaleString("en-IN")}</div>
              </div>

              <div className="pillar-box">
                <div className="label">आपातकालीन बचत (Safety Fund)</div>
                <div className="value">₹{profile.emergency_fund_inr.toLocaleString("en-IN")}</div>
              </div>

              <div className="pillar-box">
                <div className="label">ऋण बोझ अनुपात (Debt Ratio)</div>
                <div className="value">{arthScore.debt_ratio || 15.6}%</div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: FRAUD SHIELD */}
        {activeTab === "fraud" && (
          <div className="fraud-shield-view">
            <div className="emergency-banner">
              <h3>🚨 साइबर वित्तीय धोखाधड़ी आपातकालीन सहायता</h3>
              <p style={{ fontSize: "13px", color: "#991b1b", lineHeight: 1.5 }}>
                यदि आपके खाते से धोखाधड़ी से पैसे कट गए हैं या किसी ने बैंक/बिजली विभाग के नाम पर 
                OTP या UPI PIN मांगा है, तो तुरंत 1930 पर कॉल करें और बैंक को सूचित करें।
              </p>

              <div className="emergency-actions-row">
                <a href="tel:1930" className="emergency-btn call-1930">
                  <PhoneCall size={16} />
                  <span>राष्ट्रीय हेल्पलाइन 1930 डायल करें</span>
                </a>

                <a 
                  href="https://sachet.rbi.org.in/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="emergency-btn portal-sachet"
                >
                  <ExternalLink size={16} />
                  <span>आरबीआई सचेत पोर्टल (RBI Sachet)</span>
                </a>

                <a 
                  href="https://cybercrime.gov.in/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="emergency-btn portal-sachet"
                >
                  <ExternalLink size={16} />
                  <span>राष्ट्रीय साइबर अपराध रिपोर्टिंग पोर्टल</span>
                </a>
              </div>
            </div>

            <div className="info-card" style={{ marginTop: "10px" }}>
              <div className="info-card-header">
                <div className="info-card-title">प्रहरी सुरक्षा गार्ड (Prahari Fraud Sentinel)</div>
                <span className="benefit-pill" style={{ color: "#059669", background: "#ecfdf5" }}>सक्रिय (Active)</span>
              </div>
              <div className="info-card-body">
                <p>
                  अर्थसेतु का प्रहरी इंजन प्रत्येक संदेश का 30 ज्ञात धोखाधड़ी पैटर्न्स और 
                  कठोर सीडर (Cedar) नीतियों के तहत स्वचालित विश्लेषण करता है।
                </p>
                <ul style={{ paddingLeft: "18px", marginTop: "8px", display: "flex", flexDirection: "column", gap: "6px" }}>
                  <li>कदापि किसी को अपना <strong>UPI PIN</strong> या <strong>OTP</strong> न बताएं।</li>
                  <li>लोन पास कराने के नाम पर <strong>अग्रिम प्रोसेसिंग फीस</strong> न दें।</li>
                  <li>अज्ञात नंबरों से आए <strong>.apk फाइल या लिंक</strong> को डाउनलोड न करें।</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: HISTORY */}
        {activeTab === "history" && (
          <div style={{ padding: "20px" }}>
            <div className="panel-header-block" style={{ borderRadius: "12px", border: "1px solid var(--border-light)", marginBottom: "16px" }}>
              <div className="panel-title">पिछली बातचीत एवं ऑडिट इतिहास</div>
              <div className="panel-description">
                इस सत्र में पूछे गए वित्तीय प्रश्न और प्राप्त सुरक्षा परामर्श।
              </div>
            </div>

            {history.length === 0 ? (
              <div style={{ textAlign: "center", padding: "40px 20px", color: "var(--text-muted)" }}>
                अभी तक कोई प्रश्न दर्ज नहीं है। संवाद सहायक में जाकर अपना प्रश्न पूछें।
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {history.map((entry) => (
                  <div key={entry.id} className="info-card">
                    <div className="info-card-header">
                      <strong style={{ fontSize: "14px", color: "var(--gov-navy)" }}>{entry.query}</strong>
                      <span className={`security-badge ${entry.scamDetected ? "threat" : "safe"}`}>
                        {entry.scamDetected ? "धोखाधड़ी चेतावनी" : "सुरक्षित"}
                      </span>
                    </div>
                    <div className="info-card-body">
                      {entry.response}
                    </div>
                    <span className="timestamp" style={{ textAlign: "left" }}>
                      समय: {new Date(entry.timestamp).toLocaleString("hi-IN")}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 6: GUIDE */}
        {activeTab === "guide" && (
          <div className="tab-pane-container guide-container">
            {/* Guide Hero Card */}
            <div className="guide-hero-card">
              <div className="guide-hero-header">
                <div className="guide-hero-badge">
                  <BookOpen size={16} />
                  <span>नागरिक मार्गदर्शिका • User Guide</span>
                </div>
                <h2>अर्थसेतु कैसे काम करता है और इसका उपयोग कैसे करें?</h2>
                <p>
                  अर्थसेतु भारतीय नागरिकों, किसानों, रेहड़ी-पटरी विक्रेताओं और परिवारों को वित्तीय सुरक्षा, 
                  सरकारी कल्याणकारी योजनाओं और साइबर धोखाधड़ी से बचाव के लिए एक सुरक्षित, प्रमाणित डिजिटल परामर्श मंच प्रदान करता है।
                </p>
              </div>

              <div className="guide-features-strip">
                <div className="guide-feature-box">
                  <div className="guide-feature-icon safe">
                    <ShieldCheck size={20} />
                  </div>
                  <div>
                    <strong>सिडार पॉलिसी फ़ायरवॉल</strong>
                    <p>कोई भ्रामक या अवास्तविक वादा नहीं। प्रत्येक सलाह वित्तीय नियमों के अनुरूप जांची जाती है।</p>
                  </div>
                </div>

                <div className="guide-feature-box">
                  <div className="guide-feature-icon info">
                    <Volume2 size={20} />
                  </div>
                  <div>
                    <strong>सरल भाषा व बोलकर पूछें</strong>
                    <p>हिंदी, अंग्रेजी व अन्य भारतीय भाषाओं में बोलकर या लिखकर आसानी से सलाह प्राप्त करें।</p>
                  </div>
                </div>

                <div className="guide-feature-box">
                  <div className="guide-feature-icon alert">
                    <ShieldAlert size={20} />
                  </div>
                  <div>
                    <strong>30+ साइबर फ्रॉड डिटेक्शन</strong>
                    <p>बिजली बिल, लॉटरी, 7-दिन वाले लोन ऐप व ओटीपी फर्जीवाड़े की तत्काल सुरक्षा जांच।</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Interactive Scenarios Section */}
            <div className="guide-section">
              <div className="section-title-bar">
                <h3>
                  <CheckCircle2 size={18} color="var(--gov-saffron)" />
                  <span>प्रमुख परिदृश्य एवं लाइव टेस्ट (Interactive Scenarios)</span>
                </h3>
                <span className="section-subtitle">नीचे दिए गए किसी भी प्रश्न को एक क्लिक में चलाकर देखें:</span>
              </div>

              <div className="guide-scenarios-grid">
                {/* Scenario 1 */}
                <div className="guide-scenario-card">
                  <div className="scenario-card-header">
                    <span className="scenario-badge farmer">किसान कल्याण</span>
                    <h4>पीएम किसान एवं फसल बीमा पात्रता</h4>
                  </div>
                  <p className="scenario-desc">
                    छोटे व सीमांत किसानों के लिए ₹6,000 वार्षिक सहायता (PM-KISAN), किसान क्रेडिट कार्ड (KCC) और फसल बीमा की शर्तें।
                  </p>
                  <div className="scenario-prompt-box">
                    <em>&quot;मुझे पीएम किसान योजना (PM-KISAN) और फसल बीमा के लिए कैसे आवेदन करना चाहिए? मेरी जमीन 1.5 एकड़ है।&quot;</em>
                  </div>
                  <button 
                    className="scenario-action-btn"
                    onClick={() => handleTryScenario("मुझे पीएम किसान योजना (PM-KISAN) और फसल बीमा के लिए कैसे आवेदन करना चाहिए? मेरी जमीन 1.5 एकड़ है।")}
                  >
                    <span>इस प्रश्न को आज़माएं (Try This Prompt)</span>
                    <ExternalLink size={14} />
                  </button>
                </div>

                {/* Scenario 2 */}
                <div className="guide-scenario-card">
                  <div className="scenario-card-header">
                    <span className="scenario-badge vendor">लघु व्यापारी</span>
                    <h4>पीएम स्वनिधि बिना गारंटी लोन</h4>
                  </div>
                  <p className="scenario-desc">
                    रेहड़ी-पटरी व फुटपाथ विक्रेताओं के लिए ₹10,000 से ₹50,000 तक की पूंजी, 7% ब्याज सब्सिडी व डिजिटल कैशबैक लाभ।
                  </p>
                  <div className="scenario-prompt-box">
                    <em>&quot;मैं रेहड़ी-पटरी (Street Vendor) वाला हूँ, क्या मुझे पीएम स्वनिधि योजना से बिना गारंटी का लोन मिल सकता है?&quot;</em>
                  </div>
                  <button 
                    className="scenario-action-btn"
                    onClick={() => handleTryScenario("मैं रेहड़ी-पटरी (Street Vendor) वाला हूँ, क्या मुझे पीएम स्वनिधि योजना से बिना गारंटी का लोन मिल सकता है?")}
                  >
                    <span>इस प्रश्न को आज़माएं (Try This Prompt)</span>
                    <ExternalLink size={14} />
                  </button>
                </div>

                {/* Scenario 3 */}
                <div className="guide-scenario-card threat-card">
                  <div className="scenario-card-header">
                    <span className="scenario-badge fraud">साइबर सुरक्षा</span>
                    <h4>बिजली बिल कटने का फर्जी संदेश</h4>
                  </div>
                  <p className="scenario-desc">
                    नागरिकों को डराने वाले बिजली बिल एसएमएस की सुरक्षा जांच — अर्थसेतु इसे तत्काल फ्रॉड घोषित कर चेतावनी जारी करता है।
                  </p>
                  <div className="scenario-prompt-box threat-box">
                    <em>&quot;Dear consumer your electricity power will disconnect tonight at 9:30 PM because bill not updated. Call electricity officer 9876543210 immediately.&quot;</em>
                  </div>
                  <button 
                    className="scenario-action-btn threat-btn"
                    onClick={() => handleTryScenario("Dear consumer your electricity power will disconnect tonight at 9:30 PM because bill not updated. Call electricity officer 9876543210 immediately.")}
                  >
                    <span>इस फर्जीवाड़े की जांच करें (Test Fraud Shield)</span>
                    <ExternalLink size={14} />
                  </button>
                </div>

                {/* Scenario 4 */}
                <div className="guide-scenario-card threat-card">
                  <div className="scenario-card-header">
                    <span className="scenario-badge fraud">अवैध ऋण ऐप</span>
                    <h4>7-दिन वाले लोन ऐप व 120% ब्याज चेतावनी</h4>
                  </div>
                  <p className="scenario-desc">
                    अवैध चीनी व अनरजिस्टर्ड लोन ऐप्स जो फोन संपर्कों की एक्सेस मांगते हैं और अत्यधिक ब्याज वसूलते हैं — सिस्टम तुरंत चेतावनी देता है।
                  </p>
                  <div className="scenario-prompt-box threat-box">
                    <em>&quot;क्या 7 दिन वाला इंस्टेंट लोन ऐप लेना चाहिए जो 120% सालाना ब्याज मांग रहा है और कॉन्टैक्ट लिस्ट मांग रहा है?&quot;</em>
                  </div>
                  <button 
                    className="scenario-action-btn threat-btn"
                    onClick={() => handleTryScenario("क्या 7 दिन वाला इंस्टेंट लोन ऐप लेना चाहिए जो 120% सालाना ब्याज मांग रहा है और कॉन्टैक्ट लिस्ट मांग रहा है?")}
                  >
                    <span>इस अवैध लोन की जांच करें (Test Loan Shield)</span>
                    <ExternalLink size={14} />
                  </button>
                </div>

                {/* Scenario 5 */}
                <div className="guide-scenario-card">
                  <div className="scenario-card-header">
                    <span className="scenario-badge finance">अर्थ स्कोर</span>
                    <h4>आपातकालीन बचत एवं पारिवारिक बजट</h4>
                  </div>
                  <p className="scenario-desc">
                    आय व व्यय के आधार पर वित्तीय स्वास्थ्य स्कोर, 3 महीने के आपातकालीन फंड की योजना और व्यावहारिक सुझाव।
                  </p>
                  <div className="scenario-prompt-box">
                    <em>&quot;मेरी मासिक आय ₹25,000 है और खर्च ₹18,000 है, मुझे आपातकालीन फंड और बचत कैसे बनानी चाहिए?&quot;</em>
                  </div>
                  <button 
                    className="scenario-action-btn"
                    onClick={() => handleTryScenario("मेरी मासिक आय ₹25,000 है और खर्च ₹18,000 है, मुझे आपातकालीन फंड और बचत कैसे बनानी चाहिए?")}
                  >
                    <span>इस प्रश्न को आज़माएं (Try This Prompt)</span>
                    <ExternalLink size={14} />
                  </button>
                </div>

                {/* Scenario 6 */}
                <div className="guide-scenario-card">
                  <div className="scenario-card-header">
                    <span className="scenario-badge vendor">सुरक्षित पेंशन</span>
                    <h4>अटल पेंशन योजना (APY) बुढ़ापा सहारा</h4>
                  </div>
                  <p className="scenario-desc">
                    असंगठित क्षेत्र के कामगारों के लिए 60 वर्ष की आयु के बाद ₹1,000 से ₹5,000 की मासिक सरकारी गारंटीड पेंशन।
                  </p>
                  <div className="scenario-prompt-box">
                    <em>&quot;मेरी उम्र 28 वर्ष है, मुझे अटल पेंशन योजना (APY) में हर महीने ₹5000 की पेंशन के लिए कितना जमा करना होगा?&quot;</em>
                  </div>
                  <button 
                    className="scenario-action-btn"
                    onClick={() => handleTryScenario("मेरी उम्र 28 वर्ष है, मुझे अटल पेंशन योजना (APY) में हर महीने ₹5000 की पेंशन के लिए कितना जमा करना होगा?")}
                  >
                    <span>इस प्रश्न को आज़माएं (Try This Prompt)</span>
                    <ExternalLink size={14} />
                  </button>
                </div>
              </div>
            </div>

            {/* Guardrails & Verification Explanation */}
            <div className="guide-section">
              <div className="section-title-bar">
                <h3>
                  <ShieldCheck size={18} color="var(--gov-navy)" />
                  <span>सिडार पॉलिसी इंजन कैसे सुरक्षा सुनिश्चित करता है?</span>
                </h3>
              </div>

              <div className="guide-guardrails-grid">
                <div className="guardrail-card">
                  <div className="guardrail-num">1</div>
                  <div className="guardrail-body">
                    <strong>कोई गैर-कानूनी या भ्रामक गारंटी नहीं</strong>
                    <p>अर्थसेतु कभी भी &quot;100% निश्चित मुनाफा&quot;, &quot;पैसे दोगुना करने&quot;, या &quot;अवैध साहूकारों&quot; से कर्ज लेने की सलाह नहीं देता।</p>
                  </div>
                </div>

                <div className="guardrail-card">
                  <div className="guardrail-num">2</div>
                  <div className="guardrail-body">
                    <strong>विनियामक अस्वीकरण (Mandatory Disclaimers)</strong>
                    <p>किसी भी वित्तीय या ऋण योजना पर चर्चा के दौरान आरबीआई (RBI), सेबी (SEBI) या आईआरडीएआई (IRDAI) अस्वीकरण अनिवार्य रूप से संलग्न होता है।</p>
                  </div>
                </div>

                <div className="guardrail-card">
                  <div className="guardrail-num">3</div>
                  <div className="guardrail-body">
                    <strong>गोपनीयता और डेटा सुरक्षा</strong>
                    <p>हम कभी भी आपका पूरा आधार नंबर, बैंक पासवर्ड, एटीएम पिन या ओटीपी नहीं मांगते और न ही स्टोर करते हैं।</p>
                  </div>
                </div>

                <div className="guardrail-card">
                  <div className="guardrail-num">4</div>
                  <div className="guardrail-body">
                    <strong>प्रमाणित सरकारी स्रोत</strong>
                    <p>सभी योजनाएं (PM-KISAN, PM SVANidhi, APY, PMFBY) सीधे भारत सरकार के आधिकारिक पोर्टल्स से सत्यापित हैं।</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Civic Helplines Directory */}
            <div className="guide-section">
              <div className="section-title-bar">
                <h3>
                  <PhoneCall size={18} color="var(--gov-navy)" />
                  <span>आधिकारिक नागरिक हेल्पलाइन व पोर्टल (Official Emergency Helplines)</span>
                </h3>
              </div>

              <div className="helpline-directory-grid">
                <div className="helpline-entry-card emergency">
                  <div className="helpline-code">1930</div>
                  <div className="helpline-info">
                    <strong>राष्ट्रीय साइबर अपराध हेल्पलाइन (National Cybercrime)</strong>
                    <span>वित्तीय धोखाधड़ी, यूपीआई फ्रॉड या संदिग्ध लेनदेन की 24x7 तत्काल शिकायत</span>
                    <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer">cybercrime.gov.in ↗</a>
                  </div>
                </div>

                <div className="helpline-entry-card">
                  <div className="helpline-code">1915</div>
                  <div className="helpline-info">
                    <strong>राष्ट्रीय उपभोक्ता हेल्पलाइन (Consumer Helpline)</strong>
                    <span>बैंक अनुचित शुल्क, बीमा क्लेम में देरी, या ई-कॉमर्स शिकायतों हेतु</span>
                    <a href="https://consumerhelpline.gov.in" target="_blank" rel="noopener noreferrer">consumerhelpline.gov.in ↗</a>
                  </div>
                </div>

                <div className="helpline-entry-card">
                  <div className="helpline-code">1800-180-1551</div>
                  <div className="helpline-info">
                    <strong>किसान कॉल सेंटर (Kisan Call Centre)</strong>
                    <span>फसल बीमा, केसीसी ब्याज दर एवं कृषि संबंधी विशेषज्ञ सलाह (सुबह 6 से रात 10 बजे)</span>
                    <a href="https://pmkisan.gov.in" target="_blank" rel="noopener noreferrer">pmkisan.gov.in ↗</a>
                  </div>
                </div>

                <div className="helpline-entry-card">
                  <div className="helpline-code">1800-11-1979</div>
                  <div className="helpline-info">
                    <strong>पीएम स्वनिधि हेल्पलाइन (PM SVANidhi Support)</strong>
                    <span>रेहड़ी-पटरी विक्रेता ऋण आवेदन, ब्याज सब्सिडी एवं वेंडर आईडी सहायता</span>
                    <a href="https://pmsvanidhi.mohua.gov.in" target="_blank" rel="noopener noreferrer">pmsvanidhi.mohua.gov.in ↗</a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* User Profile Edit Modal */}
      {showProfileModal && (
        <div className="modal-overlay" onClick={() => setShowProfileModal(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>उपयोगकर्ता प्रोफाइल (User Profile)</h3>
              <button 
                onClick={() => setShowProfileModal(false)}
                style={{ background: "none", border: "none", fontSize: "18px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleProfileSave}>
              <div className="modal-body">
                <div className="form-grid">
                  <div className="form-group">
                    <label>पूरा नाम (Full Name)</label>
                    <input 
                      type="text" 
                      value={profile.name} 
                      onChange={(e) => setProfile(p => ({ ...p, name: e.target.value }))}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>व्यवसाय (Occupation)</label>
                    <input 
                      type="text" 
                      value={profile.occupation} 
                      onChange={(e) => setProfile(p => ({ ...p, occupation: e.target.value }))}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>मासिक आय (Monthly Income ₹)</label>
                    <input 
                      type="number" 
                      value={profile.monthly_income_inr} 
                      onChange={(e) => setProfile(p => ({ ...p, monthly_income_inr: Number(e.target.value) }))}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>मासिक खर्च (Monthly Expenses ₹)</label>
                    <input 
                      type="number" 
                      value={profile.monthly_expenses_inr} 
                      onChange={(e) => setProfile(p => ({ ...p, monthly_expenses_inr: Number(e.target.value) }))}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>ऋण ईएमआई (Monthly EMI ₹)</label>
                    <input 
                      type="number" 
                      value={profile.monthly_debt_emi_inr} 
                      onChange={(e) => setProfile(p => ({ ...p, monthly_debt_emi_inr: Number(e.target.value) }))}
                    />
                  </div>

                  <div className="form-group">
                    <label>आपातकालीन बचत (Emergency Savings ₹)</label>
                    <input 
                      type="number" 
                      value={profile.emergency_fund_inr} 
                      onChange={(e) => setProfile(p => ({ ...p, emergency_fund_inr: Number(e.target.value) }))}
                    />
                  </div>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn-secondary" onClick={() => setShowProfileModal(false)}>
                  रद्द करें
                </button>
                <button type="submit" className="btn-primary">
                  सहेजें (Save)
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
