"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function ScorePage() {
  const [session, setSession] = useState<any>(null);

  useEffect(() => {
    fetch(`${API}/api/v1/session/demo-user`).then((r) => r.json()).then(setSession).catch(() => setSession(null));
  }, []);

  const score = session?.arth_score_update || {
    score: 48,
    band: "improving",
    next_best_action: "Send a money question to update your score.",
    dimensions: {
      cashflow_stability: 11,
      risk_protection: 8,
      debt_health: 14,
      financial_awareness: 10,
      habit_progress: 5,
    },
  };
  const data = Object.entries(score.dimensions || {}).map(([name, value]) => ({name: name.replaceAll("_", " "), value}));

  return (
    <>
      <div className="topline">
        <div>
          <div className="title">Arth Score</div>
          <div className="subtitle">A five-dimension view of financial resilience.</div>
        </div>
        <div className="card" style={{minWidth: 160}}>
          <div className="metric">{score.score}</div>
          <div className="muted">{score.band}</div>
        </div>
      </div>
      <div className="grid two">
        <section className="card" style={{height: 360}}>
          <h2>Dimensions</h2>
          <ResponsiveContainer width="100%" height="85%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{fontSize: 11}} />
              <YAxis domain={[0, 20]} />
              <Tooltip />
              <Bar dataKey="value" fill="#0f766e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </section>
        <aside className="card">
          <h2>Next Action</h2>
          <p>{score.next_best_action}</p>
        </aside>
      </div>
    </>
  );
}
