"use client";

import { Search } from "lucide-react";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function SchemesPage() {
  const [occupation, setOccupation] = useState("farmer");
  const [income, setIncome] = useState("12000");
  const [schemes, setSchemes] = useState<any[]>([]);

  async function match() {
    const res = await fetch(`${API}/api/v1/chat`, {
      method: "POST",
      headers: { "ngrok-skip-browser-warning": "true","Content-Type": "application/json"},
      body: JSON.stringify({
        user_id: "demo-user",
        message: "Which schemes am I eligible for?",
        profile_updates: {occupation, monthly_income_inr: Number(income), land_ownership: occupation === "farmer"},
      }),
    });
    const data = await res.json();
    setSchemes(data.scheme_matches || data.agent_outputs?.shilpi?.schemes_to_apply || []);
  }

  return (
    <>
      <div className="topline">
        <div>
          <div className="title">Scheme Eligibility</div>
          <div className="subtitle">Match user facts to trusted welfare scheme pathways.</div>
        </div>
      </div>
      <section className="card">
        <div className="grid three">
          <label>Occupation<input className="input" value={occupation} onChange={(e) => setOccupation(e.target.value)} /></label>
          <label>Monthly income<input className="input" value={income} onChange={(e) => setIncome(e.target.value)} /></label>
          <div className="row" style={{alignItems: "end"}}><button className="button" onClick={match}><Search size={18} /> Match</button></div>
        </div>
      </section>
      <section className="list" style={{marginTop: 16}}>
        {(schemes.length ? schemes : []).map((scheme) => (
          <article className="item" key={scheme.scheme_id || scheme.name}>
            <strong>{scheme.name}</strong>
            <div className="muted">{scheme.benefit}</div>
            <a href={scheme.apply_url} target="_blank">Open official site</a>
          </article>
        ))}
      </section>
    </>
  );
}
