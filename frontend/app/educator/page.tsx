"use client";

import { AlertTriangle, CheckCircle2, Users } from "lucide-react";

const cards = [
  {label: "Learners reached", value: "128", icon: Users},
  {label: "Scam alerts generated", value: "37", icon: AlertTriangle},
  {label: "Scheme matches", value: "84", icon: CheckCircle2},
];

export default function EducatorPage() {
  return (
    <>
      <div className="topline">
        <div>
          <div className="title">NGO Command Center</div>
          <div className="subtitle">Track community literacy, scam risk, and scheme access activity.</div>
        </div>
      </div>
      <div className="grid three">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <section className="card" key={card.label}>
              <Icon size={20} />
              <div className="metric">{card.value}</div>
              <div className="muted">{card.label}</div>
            </section>
          );
        })}
      </div>
      <section className="card" style={{marginTop: 16}}>
        <h2>Field Queue</h2>
        <div className="list">
          <div className="item"><strong>High risk:</strong> KYC/OTP scam messages circulating in WhatsApp group.</div>
          <div className="item"><strong>Follow up:</strong> Farmers matched with PMFBY and PM-KISAN need document help.</div>
          <div className="item"><strong>Workshop:</strong> Explain UPI collect requests and QR receive-money fraud.</div>
        </div>
      </section>
    </>
  );
}
