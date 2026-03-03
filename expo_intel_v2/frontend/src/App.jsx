import { useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";
import { apiGet, apiPost, toCsvUrl } from "./api";

const tabs = [
  "Walking Dashboard",
  "Deep Evaluation Dashboard",
  "Strategic Ranking Board",
  "Hall Heat Map Visualization",
  "Post-Show Follow-Up Queue"
];

const categoryWeights = {
  meat: 10,
  sausage: 10,
  jerky: 10,
  "protein snack": 7,
  collagen: 5,
  functional: 5,
  "plant protein": 3,
  "ingredient supplier": 4,
  equipment: 2
};
const formatWeights = { stick: 5, snack: 5, "sausage link": 5, patty: 4, chub: 4, "frozen entrée": 2 };
const claimsWeights = { organic: 3, roc: 5, "grass-fed": 4, regenerative: 6, "nitrate-free": 2, "high protein": 3 };
const scaleWeights = { small: 5, mid: 10, national: 20 };
const channelWeights = { club: 15, costco: 15, "whole foods": 10, "national retail": 12, dtc: 5 };

function App() {
  const [activeTab, setActiveTab] = useState(tabs[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [walkRows, setWalkRows] = useState([]);
  const [deepRows, setDeepRows] = useState([]);
  const [ranking, setRanking] = useState([]);
  const [heatMapRows, setHeatMapRows] = useState([]);
  const [queue, setQueue] = useState([]);

  const [filters, setFilters] = useState({
    meat_forward_only: false,
    organic_only: false,
    direct_competitors_only: false,
    high_partnership_only: false
  });

  const [walkForm, setWalkForm] = useState({
    company_name: "",
    booth_number: "",
    hall: "",
    category_tags: [],
    protein_signal_score: 3,
    competitive_threat_score: 3,
    usda_flag: false,
    organic_flag: false,
    sqf_flag: false,
    regenerative_flag: false,
    emerging_brand_flag: false,
    quick_notes: "",
    follow_up_flag: "revisit"
  });

  const [deepForm, setDeepForm] = useState({
    company_name: "",
    booth_number: "",
    contact_name: "",
    contact_email: "",
    contact_role: "",
    website: "",
    core_skus: "",
    format_type: "",
    pack_size: "",
    price_per_unit: "",
    claims_tags: [],
    manufacturing_type: "unknown",
    certifications: [],
    estimated_scale: "small",
    channel_presence: [],
    direct_competitor_flag: false,
    closest_charcut_sku: "",
    strategic_fit_score: 3,
    competitive_threat_score: 3,
    partnership_potential_score: 3,
    strength_notes: "",
    weakness_notes: "",
    action_plan: [],
    post_show_priority: "tier3"
  });

  const walkPreview = useMemo(() => scoreWalkPreview(walkForm), [walkForm]);
  const deepPreview = useMemo(() => scoreDeepPreview(deepForm), [deepForm]);

  async function refreshAll() {
    setLoading(true);
    setError("");
    try {
      const walkQ = `?meat_forward_only=${filters.meat_forward_only}&organic_only=${filters.organic_only}`;
      const deepQ = `?direct_competitors_only=${filters.direct_competitors_only}&high_partnership_only=${filters.high_partnership_only}`;
      const [walk, deep, rank, heat, follow] = await Promise.all([
        apiGet(`/walk-scans${walkQ}`),
        apiGet(`/deep-evals${deepQ}`),
        apiGet("/analytics/strategic-ranking"),
        apiGet("/analytics/hall-heat-map"),
        apiGet("/analytics/follow-up-queue")
      ]);
      setWalkRows(walk);
      setDeepRows(deep);
      setRanking(rank);
      setHeatMapRows(heat);
      setQueue(follow);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  async function submitWalk(e) {
    e.preventDefault();
    await apiPost("/walk-scans", walkForm);
    setWalkForm({ ...walkForm, company_name: "", booth_number: "", quick_notes: "" });
    await refreshAll();
  }

  async function submitDeep(e) {
    e.preventDefault();
    await apiPost("/deep-evals", { ...deepForm, price_per_unit: Number(deepForm.price_per_unit || 0) || null });
    setDeepForm({ ...deepForm, company_name: "", booth_number: "", contact_name: "", contact_email: "" });
    await refreshAll();
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Expo Intelligence System</h1>
        <p>Fast scan + deep eval + strategic scoring (PRS / CTI / POS / SPS)</p>
      </header>

      <div className="tabs">
        {tabs.map((t) => (
          <button key={t} className={activeTab === t ? "tab active" : "tab"} onClick={() => setActiveTab(t)}>
            {t}
          </button>
        ))}
      </div>

      <section className="filters">
        <label><input type="checkbox" checked={filters.meat_forward_only} onChange={(e) => setFilters({ ...filters, meat_forward_only: e.target.checked })} /> Meat-forward only</label>
        <label><input type="checkbox" checked={filters.organic_only} onChange={(e) => setFilters({ ...filters, organic_only: e.target.checked })} /> Organic only</label>
        <label><input type="checkbox" checked={filters.direct_competitors_only} onChange={(e) => setFilters({ ...filters, direct_competitors_only: e.target.checked })} /> Direct competitors only</label>
        <label><input type="checkbox" checked={filters.high_partnership_only} onChange={(e) => setFilters({ ...filters, high_partnership_only: e.target.checked })} /> High partnership potential only</label>
        <button onClick={refreshAll}>Refresh</button>
      </section>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Loading...</div>}

      {activeTab === "Walking Dashboard" && (
        <div className="panel">
          <h2>Walking Dashboard (Rapid Scan)</h2>
          <form onSubmit={submitWalk} className="grid-form">
            <input placeholder="Company Name" required value={walkForm.company_name} onChange={(e) => setWalkForm({ ...walkForm, company_name: e.target.value })} />
            <input placeholder="Booth Number" value={walkForm.booth_number} onChange={(e) => setWalkForm({ ...walkForm, booth_number: e.target.value })} />
            <input placeholder="Hall" value={walkForm.hall} onChange={(e) => setWalkForm({ ...walkForm, hall: e.target.value })} />
            <input placeholder="Category tags (comma separated)" value={walkForm.category_tags.join(", ")} onChange={(e) => setWalkForm({ ...walkForm, category_tags: csvList(e.target.value) })} />
            <label>Protein Signal
              <input type="number" min="1" max="5" value={walkForm.protein_signal_score} onChange={(e) => setWalkForm({ ...walkForm, protein_signal_score: Number(e.target.value) })} />
            </label>
            <label>Threat
              <input type="number" min="1" max="5" value={walkForm.competitive_threat_score} onChange={(e) => setWalkForm({ ...walkForm, competitive_threat_score: Number(e.target.value) })} />
            </label>
            <input placeholder="Quick Notes" value={walkForm.quick_notes} onChange={(e) => setWalkForm({ ...walkForm, quick_notes: e.target.value })} />
            <select value={walkForm.follow_up_flag} onChange={(e) => setWalkForm({ ...walkForm, follow_up_flag: e.target.value })}>
              <option value="revisit">revisit</option>
              <option value="deep_dive">deep_dive</option>
              <option value="skip">skip</option>
            </select>
            <label><input type="checkbox" checked={walkForm.usda_flag} onChange={(e) => setWalkForm({ ...walkForm, usda_flag: e.target.checked })} /> USDA</label>
            <label><input type="checkbox" checked={walkForm.organic_flag} onChange={(e) => setWalkForm({ ...walkForm, organic_flag: e.target.checked })} /> Organic</label>
            <label><input type="checkbox" checked={walkForm.sqf_flag} onChange={(e) => setWalkForm({ ...walkForm, sqf_flag: e.target.checked })} /> SQF</label>
            <label><input type="checkbox" checked={walkForm.regenerative_flag} onChange={(e) => setWalkForm({ ...walkForm, regenerative_flag: e.target.checked })} /> Regenerative</label>
            <label><input type="checkbox" checked={walkForm.emerging_brand_flag} onChange={(e) => setWalkForm({ ...walkForm, emerging_brand_flag: e.target.checked })} /> Emerging Brand</label>
            <button type="submit">Save Scan</button>
          </form>
          <ScorePreview preview={walkPreview} />
          <SimpleTable rows={walkRows} />
          <a href={toCsvUrl("/analytics/export/walk.csv")} target="_blank" rel="noreferrer">Export Walk CSV</a>
        </div>
      )}

      {activeTab === "Deep Evaluation Dashboard" && (
        <div className="panel">
          <h2>Deep Evaluation Dashboard</h2>
          <form onSubmit={submitDeep} className="grid-form">
            <input placeholder="Company Name" required value={deepForm.company_name} onChange={(e) => setDeepForm({ ...deepForm, company_name: e.target.value })} />
            <input placeholder="Booth Number" value={deepForm.booth_number} onChange={(e) => setDeepForm({ ...deepForm, booth_number: e.target.value })} />
            <input placeholder="Contact Name" value={deepForm.contact_name} onChange={(e) => setDeepForm({ ...deepForm, contact_name: e.target.value })} />
            <input placeholder="Contact Email" value={deepForm.contact_email} onChange={(e) => setDeepForm({ ...deepForm, contact_email: e.target.value })} />
            <input placeholder="Contact Role" value={deepForm.contact_role} onChange={(e) => setDeepForm({ ...deepForm, contact_role: e.target.value })} />
            <input placeholder="Website" value={deepForm.website} onChange={(e) => setDeepForm({ ...deepForm, website: e.target.value })} />
            <input placeholder="Core SKUs" value={deepForm.core_skus} onChange={(e) => setDeepForm({ ...deepForm, core_skus: e.target.value })} />
            <input placeholder="Format Type" value={deepForm.format_type} onChange={(e) => setDeepForm({ ...deepForm, format_type: e.target.value })} />
            <input placeholder="Pack Size" value={deepForm.pack_size} onChange={(e) => setDeepForm({ ...deepForm, pack_size: e.target.value })} />
            <input placeholder="Price Per Unit" type="number" step="0.01" value={deepForm.price_per_unit} onChange={(e) => setDeepForm({ ...deepForm, price_per_unit: e.target.value })} />
            <input placeholder="Claims tags (comma separated)" value={deepForm.claims_tags.join(", ")} onChange={(e) => setDeepForm({ ...deepForm, claims_tags: csvList(e.target.value) })} />
            <input placeholder="Certifications (comma separated)" value={deepForm.certifications.join(", ")} onChange={(e) => setDeepForm({ ...deepForm, certifications: csvList(e.target.value) })} />
            <input placeholder="Channel Presence (comma separated)" value={deepForm.channel_presence.join(", ")} onChange={(e) => setDeepForm({ ...deepForm, channel_presence: csvList(e.target.value) })} />
            <select value={deepForm.manufacturing_type} onChange={(e) => setDeepForm({ ...deepForm, manufacturing_type: e.target.value })}>
              <option value="unknown">unknown</option>
              <option value="self">self</option>
              <option value="co_pack">co_pack</option>
            </select>
            <select value={deepForm.estimated_scale} onChange={(e) => setDeepForm({ ...deepForm, estimated_scale: e.target.value })}>
              <option value="small">small</option>
              <option value="mid">mid</option>
              <option value="national">national</option>
            </select>
            <label><input type="checkbox" checked={deepForm.direct_competitor_flag} onChange={(e) => setDeepForm({ ...deepForm, direct_competitor_flag: e.target.checked })} /> Direct Competitor</label>
            <input placeholder="Closest Charcut SKU" value={deepForm.closest_charcut_sku} onChange={(e) => setDeepForm({ ...deepForm, closest_charcut_sku: e.target.value })} />
            <label>Strategic Fit <input type="number" min="1" max="5" value={deepForm.strategic_fit_score} onChange={(e) => setDeepForm({ ...deepForm, strategic_fit_score: Number(e.target.value) })} /></label>
            <label>Threat <input type="number" min="1" max="5" value={deepForm.competitive_threat_score} onChange={(e) => setDeepForm({ ...deepForm, competitive_threat_score: Number(e.target.value) })} /></label>
            <label>Partnership <input type="number" min="1" max="5" value={deepForm.partnership_potential_score} onChange={(e) => setDeepForm({ ...deepForm, partnership_potential_score: Number(e.target.value) })} /></label>
            <input placeholder="Strength Notes" value={deepForm.strength_notes} onChange={(e) => setDeepForm({ ...deepForm, strength_notes: e.target.value })} />
            <input placeholder="Weakness Notes" value={deepForm.weakness_notes} onChange={(e) => setDeepForm({ ...deepForm, weakness_notes: e.target.value })} />
            <input placeholder="Action Plan (comma separated)" value={deepForm.action_plan.join(", ")} onChange={(e) => setDeepForm({ ...deepForm, action_plan: csvList(e.target.value) })} />
            <button type="submit">Save Deep Eval</button>
          </form>
          <ScorePreview preview={deepPreview} />
          <SimpleTable rows={deepRows} />
          <a href={toCsvUrl("/analytics/export/deep.csv")} target="_blank" rel="noreferrer">Export Deep Eval CSV</a>
        </div>
      )}

      {activeTab === "Strategic Ranking Board" && (
        <div className="panel">
          <h2>Strategic Ranking Board</h2>
          <SimpleTable rows={ranking} />
        </div>
      )}

      {activeTab === "Hall Heat Map Visualization" && (
        <div className="panel">
          <h2>Hall Heat Map Visualization</h2>
          <Plot
            data={[
              {
                type: "bar",
                x: heatMapRows.map((r) => r.hall),
                y: heatMapRows.map((r) => r.avg_sps),
                marker: { color: heatMapRows.map((r) => colorMap(r.heat_color)) }
              }
            ]}
            layout={{ title: "Average SPS by Hall", yaxis: { title: "Avg SPS" }, autosize: true }}
            style={{ width: "100%", height: "360px" }}
            useResizeHandler
          />
          <SimpleTable rows={heatMapRows} />
        </div>
      )}

      {activeTab === "Post-Show Follow-Up Queue" && (
        <div className="panel">
          <h2>Post-Show Follow-Up Queue (Tier 1)</h2>
          <SimpleTable rows={queue} />
        </div>
      )}
    </div>
  );
}

function ScorePreview({ preview }) {
  return (
    <div className="preview">
      <strong>Live Score Preview:</strong>
      <span> PRS: {nullable(preview.prs_score)} </span>
      <span> CTI: {nullable(preview.cti_score)} </span>
      <span> POS: {nullable(preview.pos_score)} </span>
      <span> SPS: {nullable(preview.sps_score)} </span>
      <span> Tier: {preview.tier || "n/a"} </span>
    </div>
  );
}

function SimpleTable({ rows }) {
  if (!rows?.length) return <p>No data.</p>;
  const keys = Object.keys(rows[0]);
  return (
    <div className="table-wrap">
      <table>
        <thead><tr>{keys.map((k) => <th key={k}>{k}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, idx) => (
            <tr key={idx}>
              {keys.map((k) => <td key={k}>{renderCell(r[k])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function renderCell(v) {
  if (Array.isArray(v)) return v.join(", ");
  if (typeof v === "object" && v !== null) return JSON.stringify(v);
  return String(v ?? "");
}

function csvList(v) {
  return v.split(",").map((x) => x.trim()).filter(Boolean);
}

function nullable(v) {
  return v === null || v === undefined ? "n/a" : Number(v).toFixed(1);
}

function colorMap(c) {
  const m = { Red: "#d62728", Orange: "#ff7f0e", Yellow: "#f2c744", "Light Green": "#78c679", Gray: "#9aa0a6" };
  return m[c] || "#9aa0a6";
}

function scoreWalkPreview(form) {
  if (!form.protein_signal_score || !form.category_tags.length) return { prs_score: null, cti_score: null, pos_score: null, sps_score: null, tier: null };
  const prs = Math.min(
    100,
    (Number(form.protein_signal_score) * 3) +
      categoryWeight(form.category_tags) +
      0 +
      (form.organic_flag ? 3 : 0) +
      (form.regenerative_flag ? 6 : 0)
  );
  return { prs_score: prs, cti_score: null, pos_score: null, sps_score: null, tier: null };
}

function scoreDeepPreview(form) {
  const prs = form.strategic_fit_score && form.claims_tags.length ? Math.min(100, Number(form.strategic_fit_score) * 3 + formatWeight(form.format_type) + claimsWeight(form.claims_tags)) : null;
  const cti = form.competitive_threat_score && form.estimated_scale
    ? Math.min(100, Number(form.competitive_threat_score) * 5 + (form.direct_competitor_flag ? 20 : 0) + (scaleWeights[form.estimated_scale] || 0) + channelWeight(form.channel_presence))
    : null;
  const pos = form.partnership_potential_score && form.manufacturing_type
    ? Math.min(100, Number(form.partnership_potential_score) * 5 + (form.manufacturing_type === "co_pack" ? 15 : 0) + certWeight(form.certifications))
    : null;
  const sps = prs !== null && cti !== null && pos !== null ? (prs * 0.4) + (cti * 0.35) + (pos * 0.25) : null;
  return { prs_score: prs, cti_score: cti, pos_score: pos, sps_score: sps, tier: sps === null ? null : (sps >= 75 ? "tier1" : sps >= 50 ? "tier2" : "tier3") };
}

function categoryWeight(tags) {
  return Math.max(0, ...tags.map((t) => categoryWeights[String(t).toLowerCase()] || 0));
}
function formatWeight(fmt) {
  const f = String(fmt || "").toLowerCase();
  for (const key of Object.keys(formatWeights)) {
    if (f.includes(key)) return formatWeights[key];
  }
  return 0;
}
function claimsWeight(tags) {
  return tags.reduce((n, t) => n + (claimsWeights[String(t).toLowerCase()] || 0), 0);
}
function certWeight(tags) {
  return tags.reduce((n, t) => {
    const key = String(t).toLowerCase();
    if (key === "usda" || key === "organic" || key === "sqf 9" || key === "sqf") return n + 5;
    return n;
  }, 0);
}
function channelWeight(tags) {
  return tags.reduce((n, t) => n + (channelWeights[String(t).toLowerCase()] || 0), 0);
}

export default App;

