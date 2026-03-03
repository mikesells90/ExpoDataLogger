import { useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";
import { apiGet, apiPost, toCsvUrl } from "./api";

const TABS = [
  "Walking Dashboard",
  "Deep Evaluation Dashboard",
  "Strategic Ranking Board",
  "Heat Map",
  "Follow-up Queue"
];

const WALK_TAGS = [
  "Meat/Jerky/Sausage",
  "Protein Snack",
  "Collagen/Functional Protein",
  "Plant Protein",
  "Frozen",
  "Refrigerated",
  "Shelf Stable",
  "Organic/ROC/Regenerative",
  "Co-Manufacturer",
  "Ingredient Supplier",
  "Equipment/Tech",
  "Distributor/Broker",
  "Retail/Buyer"
];

const CLAIMS_TAGS = [
  "Organic", "ROC", "Grass-fed", "Regenerative", "Nitrate-free", "No Sugar", "High Protein", "Keto",
  "Paleo", "Gluten-free", "Dairy-free", "Low sodium", "Clean label", "No antibiotics", "No hormones"
];

const CHANNEL_OPTIONS = ["Retail", "Club", "Foodservice", "DTC", "Amazon", "Meal Kit", "Distribution", "International"];
const ACTION_OPTIONS = ["Email follow-up", "LinkedIn connect", "Request samples", "Request spec sheet", "Pricing follow-up", "Schedule post-show call", "Introduce to buyer", "Explore co-pack"];

function App() {
  const [tab, setTab] = useState(TABS[0]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const [walkRows, setWalkRows] = useState([]);
  const [deepRows, setDeepRows] = useState([]);
  const [rankingRows, setRankingRows] = useState([]);
  const [heatRows, setHeatRows] = useState([]);
  const [queueRows, setQueueRows] = useState([]);
  const [hallRows, setHallRows] = useState([]);
  const [selectedHall, setSelectedHall] = useState("");

  const [filters, setFilters] = useState({
    meat_forward_only: false,
    organic_only: false,
    direct_competitors_only: false,
    high_partnership_only: false,
    tier1_only: false,
    competitor_only: false,
    hall: ""
  });

  const [walkForm, setWalkForm] = useState({
    company_name: "",
    booth_number: "",
    hall: "",
    category_tags: [],
    protein_signal_score: 3,
    competitive_threat_score: 3,
    follow_up_flag: "revisit",
    usda_flag: false,
    organic_flag: false,
    sqf_flag: false,
    regenerative_flag: false,
    emerging_brand_flag: false,
    quick_notes: ""
  });

  const [deepForm, setDeepForm] = useState({
    company_name: "",
    booth_number: "",
    hall: "",
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
    kill_step_type: "unknown",
    channel_presence: [],
    direct_competitor_flag: false,
    closest_charcut_sku: "",
    differentiator_notes: "",
    weakness_notes: "",
    what_they_do_better: "",
    what_we_do_better: "",
    strategic_fit_score: 3,
    competitive_threat_score: 3,
    partnership_potential_score: 3,
    action_plan: [],
    post_show_priority: "tier3",
    full_notes: ""
  });

  const walkPreview = useMemo(() => previewWalk(walkForm), [walkForm]);
  const deepPreview = useMemo(() => previewDeep(deepForm), [deepForm]);

  async function refreshData() {
    setBusy(true);
    setError("");
    try {
      const walkQ = `?meat_forward_only=${filters.meat_forward_only}&organic_only=${filters.organic_only}`;
      const deepQ = `?direct_competitors_only=${filters.direct_competitors_only}&high_partnership_only=${filters.high_partnership_only}`;
      const rankingQ = `?tier1_only=${filters.tier1_only}&competitor_only=${filters.competitor_only}&hall=${encodeURIComponent(filters.hall || "")}`;
      const heatQ = `?tier1_only=${filters.tier1_only}&meat_only=${filters.meat_forward_only}&organic_only=${filters.organic_only}`;
      const [walk, deep, ranking, heat, queue] = await Promise.all([
        apiGet(`/walk-scans${walkQ}`),
        apiGet(`/deep-evals${deepQ}`),
        apiGet(`/analytics/strategic-ranking${rankingQ}`),
        apiGet(`/analytics/hall-heat-map${heatQ}`),
        apiGet("/analytics/follow-up-queue")
      ]);
      setWalkRows(walk);
      setDeepRows(deep);
      setRankingRows(ranking);
      setHeatRows(heat);
      setQueueRows(queue);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    refreshData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  useEffect(() => {
    if (!selectedHall) {
      setHallRows([]);
      return;
    }
    apiGet(`/analytics/hall/${encodeURIComponent(selectedHall)}/exhibitors`)
      .then(setHallRows)
      .catch((err) => setError(err.message));
  }, [selectedHall]);

  async function submitWalk(event) {
    event.preventDefault();
    await apiPost("/walk-scans", walkForm);
    setWalkForm({ ...walkForm, company_name: "", booth_number: "", quick_notes: "" });
    refreshData();
  }

  async function submitDeep(event) {
    event.preventDefault();
    await apiPost("/deep-evals", { ...deepForm, price_per_unit: Number(deepForm.price_per_unit || 0) || null });
    setDeepForm({ ...deepForm, company_name: "", contact_name: "", contact_email: "" });
    refreshData();
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Expo Intelligence System</h1>
        <p>Expo West 2026: Walking triage, in-booth evals, SPS ranking, and hall heat map.</p>
      </header>

      <div className="tabs">
        {TABS.map((name) => (
          <button key={name} className={tab === name ? "tab active" : "tab"} onClick={() => setTab(name)}>
            {name}
          </button>
        ))}
      </div>

      <section className="filters">
        <label><input type="checkbox" checked={filters.meat_forward_only} onChange={(e) => setFilters({ ...filters, meat_forward_only: e.target.checked })} /> Meat-forward only</label>
        <label><input type="checkbox" checked={filters.organic_only} onChange={(e) => setFilters({ ...filters, organic_only: e.target.checked })} /> Organic only</label>
        <label><input type="checkbox" checked={filters.direct_competitors_only} onChange={(e) => setFilters({ ...filters, direct_competitors_only: e.target.checked })} /> Direct competitors only</label>
        <label><input type="checkbox" checked={filters.high_partnership_only} onChange={(e) => setFilters({ ...filters, high_partnership_only: e.target.checked })} /> High partnership potential only</label>
        <label><input type="checkbox" checked={filters.tier1_only} onChange={(e) => setFilters({ ...filters, tier1_only: e.target.checked })} /> Tier1 only</label>
        <button onClick={refreshData}>Refresh</button>
      </section>

      {error && <div className="error">{error}</div>}
      {busy && <div className="loading">Loading...</div>}

      {tab === "Walking Dashboard" && (
        <div className="panel">
          <h2>Walking Mode Entry</h2>
          <form className="grid-form" onSubmit={submitWalk}>
            <input required placeholder="Company Name" value={walkForm.company_name} onChange={(e) => setWalkForm({ ...walkForm, company_name: e.target.value })} />
            <input placeholder="Booth Number" value={walkForm.booth_number} onChange={(e) => setWalkForm({ ...walkForm, booth_number: e.target.value })} />
            <input placeholder="Hall" value={walkForm.hall} onChange={(e) => setWalkForm({ ...walkForm, hall: e.target.value })} />
            <TagMulti title="Category Tags" options={WALK_TAGS} value={walkForm.category_tags} onChange={(value) => setWalkForm({ ...walkForm, category_tags: value })} />
            <RangeField title="Protein Signal" value={walkForm.protein_signal_score} onChange={(value) => setWalkForm({ ...walkForm, protein_signal_score: value })} />
            <RangeField title="Threat Signal" value={walkForm.competitive_threat_score} onChange={(value) => setWalkForm({ ...walkForm, competitive_threat_score: value })} />
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
            <textarea maxLength={500} placeholder="Quick notes (max 500)" value={walkForm.quick_notes} onChange={(e) => setWalkForm({ ...walkForm, quick_notes: e.target.value })} />
            <button type="submit">Save & Clear</button>
          </form>
          <ScorePreview preview={walkPreview} />
          <SimpleTable rows={walkRows} />
          <ExportLinks />
        </div>
      )}

      {tab === "Deep Evaluation Dashboard" && (
        <div className="panel">
          <h2>In-Booth Mode Entry</h2>
          <form className="grid-form" onSubmit={submitDeep}>
            <input required placeholder="Company Name" value={deepForm.company_name} onChange={(e) => setDeepForm({ ...deepForm, company_name: e.target.value })} />
            <input placeholder="Booth Number" value={deepForm.booth_number} onChange={(e) => setDeepForm({ ...deepForm, booth_number: e.target.value })} />
            <input placeholder="Hall" value={deepForm.hall} onChange={(e) => setDeepForm({ ...deepForm, hall: e.target.value })} />
            <input placeholder="Contact Name" value={deepForm.contact_name} onChange={(e) => setDeepForm({ ...deepForm, contact_name: e.target.value })} />
            <input placeholder="Contact Email" value={deepForm.contact_email} onChange={(e) => setDeepForm({ ...deepForm, contact_email: e.target.value })} />
            <input placeholder="Contact Role" value={deepForm.contact_role} onChange={(e) => setDeepForm({ ...deepForm, contact_role: e.target.value })} />
            <input placeholder="Website" value={deepForm.website} onChange={(e) => setDeepForm({ ...deepForm, website: e.target.value })} />
            <textarea placeholder="Core SKUs" value={deepForm.core_skus} onChange={(e) => setDeepForm({ ...deepForm, core_skus: e.target.value })} />
            <input placeholder="Format Type" value={deepForm.format_type} onChange={(e) => setDeepForm({ ...deepForm, format_type: e.target.value })} />
            <input placeholder="Pack Size" value={deepForm.pack_size} onChange={(e) => setDeepForm({ ...deepForm, pack_size: e.target.value })} />
            <input type="number" step="0.01" placeholder="Price per Unit" value={deepForm.price_per_unit} onChange={(e) => setDeepForm({ ...deepForm, price_per_unit: e.target.value })} />
            <TagMulti title="Claims Tags" options={CLAIMS_TAGS} value={deepForm.claims_tags} onChange={(value) => setDeepForm({ ...deepForm, claims_tags: value })} />
            <TagMulti title="Certifications" options={["USDA", "SQF", "BRC", "Organic"]} value={deepForm.certifications} onChange={(value) => setDeepForm({ ...deepForm, certifications: value })} />
            <TagMulti title="Channel Presence" options={CHANNEL_OPTIONS} value={deepForm.channel_presence} onChange={(value) => setDeepForm({ ...deepForm, channel_presence: value })} />
            <TagMulti title="Action Plan" options={ACTION_OPTIONS} value={deepForm.action_plan} onChange={(value) => setDeepForm({ ...deepForm, action_plan: value })} />
            <select value={deepForm.manufacturing_type} onChange={(e) => setDeepForm({ ...deepForm, manufacturing_type: e.target.value })}><option value="self">self</option><option value="co_pack">co_pack</option><option value="unknown">unknown</option></select>
            <select value={deepForm.estimated_scale} onChange={(e) => setDeepForm({ ...deepForm, estimated_scale: e.target.value })}><option value="small">small</option><option value="mid">mid</option><option value="national">national</option></select>
            <input placeholder="Kill Step Type" value={deepForm.kill_step_type} onChange={(e) => setDeepForm({ ...deepForm, kill_step_type: e.target.value })} />
            <label><input type="checkbox" checked={deepForm.direct_competitor_flag} onChange={(e) => setDeepForm({ ...deepForm, direct_competitor_flag: e.target.checked })} /> Direct competitor</label>
            <input placeholder="Closest Charcut SKU" value={deepForm.closest_charcut_sku} onChange={(e) => setDeepForm({ ...deepForm, closest_charcut_sku: e.target.value })} />
            <textarea placeholder="Differentiator notes" value={deepForm.differentiator_notes} onChange={(e) => setDeepForm({ ...deepForm, differentiator_notes: e.target.value })} />
            <textarea placeholder="Weakness notes" value={deepForm.weakness_notes} onChange={(e) => setDeepForm({ ...deepForm, weakness_notes: e.target.value })} />
            <textarea placeholder="What they do better" value={deepForm.what_they_do_better} onChange={(e) => setDeepForm({ ...deepForm, what_they_do_better: e.target.value })} />
            <textarea placeholder="What we do better" value={deepForm.what_we_do_better} onChange={(e) => setDeepForm({ ...deepForm, what_we_do_better: e.target.value })} />
            <RangeField title="Strategic Fit" value={deepForm.strategic_fit_score} onChange={(value) => setDeepForm({ ...deepForm, strategic_fit_score: value })} />
            <RangeField title="Threat" value={deepForm.competitive_threat_score} onChange={(value) => setDeepForm({ ...deepForm, competitive_threat_score: value })} />
            <RangeField title="Partnership" value={deepForm.partnership_potential_score} onChange={(value) => setDeepForm({ ...deepForm, partnership_potential_score: value })} />
            <select value={deepForm.post_show_priority} onChange={(e) => setDeepForm({ ...deepForm, post_show_priority: e.target.value })}>
              <option value="tier1">tier1</option><option value="tier2">tier2</option><option value="tier3">tier3</option>
            </select>
            <textarea placeholder="Full Notes" value={deepForm.full_notes} onChange={(e) => setDeepForm({ ...deepForm, full_notes: e.target.value })} />
            <button type="submit">Save Deep Eval</button>
          </form>
          <ScorePreview preview={deepPreview} />
          <SimpleTable rows={deepRows} />
          <ExportLinks />
        </div>
      )}

      {tab === "Strategic Ranking Board" && (
        <div className="panel">
          <h2>Strategic Ranking Board (deduped company+booth)</h2>
          <SimpleTable rows={rankingRows} />
          <ExportLinks />
        </div>
      )}

      {tab === "Heat Map" && (
        <div className="panel">
          <h2>Hall Heat Map</h2>
          <Plot
            data={[
              {
                type: "bar",
                x: heatRows.map((r) => r.hall),
                y: heatRows.map((r) => r.avg_sps),
                marker: { color: heatRows.map((r) => heatColor(r.heat_color)) },
                customdata: heatRows.map((r) => r.hall),
                hovertemplate: "Hall %{x}<br>Avg SPS %{y}<extra></extra>"
              }
            ]}
            layout={{ title: "Avg SPS by Hall", autosize: true, yaxis: { title: "Avg SPS" } }}
            style={{ width: "100%", height: 360 }}
            useResizeHandler
            onClick={(e) => {
              const hall = e?.points?.[0]?.customdata;
              if (hall) setSelectedHall(hall);
            }}
          />
          <SimpleTable rows={heatRows} />
          <label>Hall Drill-down</label>
          <select value={selectedHall} onChange={(e) => setSelectedHall(e.target.value)}>
            <option value="">Select hall</option>
            {heatRows.map((h) => <option key={h.hall} value={h.hall}>{h.hall}</option>)}
          </select>
          <SimpleTable rows={hallRows} />
        </div>
      )}

      {tab === "Follow-up Queue" && (
        <div className="panel">
          <h2>Post-Show Follow-up Queue (Tier1)</h2>
          <SimpleTable rows={queueRows} />
          <ExportLinks />
        </div>
      )}
    </div>
  );
}

function TagMulti({ title, options, value, onChange }) {
  return (
    <div>
      <strong>{title}</strong>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 6 }}>
        {options.map((opt) => {
          const active = value.includes(opt);
          return (
            <button
              type="button"
              key={opt}
              style={{ width: "auto", padding: "6px 10px", background: active ? "#123b73" : "#ecf1f9", color: active ? "white" : "#123b73" }}
              onClick={() => onChange(active ? value.filter((v) => v !== opt) : [...value, opt])}
            >
              {opt}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function RangeField({ title, value, onChange }) {
  return (
    <label>{title}
      <input type="range" min="1" max="5" value={value} onChange={(e) => onChange(Number(e.target.value))} />
      <div>{value}</div>
    </label>
  );
}

function ScorePreview({ preview }) {
  return (
    <div className="preview">
      <strong>Live Score Preview</strong>
      <span>PRS: {preview.prs_score}</span>
      <span>CTI: {preview.cti_score}</span>
      <span>POS: {preview.pos_score}</span>
      <span>SPS: {preview.sps_score}</span>
      <span>Tier: {preview.tier}</span>
      <span>Confidence: {preview.score_confidence}</span>
    </div>
  );
}

function ExportLinks() {
  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 8 }}>
      <a href={toCsvUrl("/analytics/export/walk.csv")} target="_blank" rel="noreferrer">expo_walk_scan.csv</a>
      <a href={toCsvUrl("/analytics/export/deep.csv")} target="_blank" rel="noreferrer">expo_deep_eval.csv</a>
      <a href={toCsvUrl("/analytics/export/combined_rankings.csv")} target="_blank" rel="noreferrer">combined_rankings.csv</a>
      <a href={toCsvUrl("/analytics/export/all.json")} target="_blank" rel="noreferrer">all.json</a>
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
          {rows.map((row, idx) => (
            <tr key={idx}>
              {keys.map((key) => <td key={key}>{renderCell(row[key])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function renderCell(v) {
  if (Array.isArray(v)) return v.join(", ");
  if (v && typeof v === "object") return JSON.stringify(v);
  return String(v ?? "");
}

function heatColor(value) {
  const map = { red: "#c62828", orange: "#ef6c00", yellow: "#fdd835", light_green: "#7cb342", gray: "#9e9e9e" };
  return map[value] || "#9e9e9e";
}

function previewWalk(form) {
  const prs = Math.min(100, ((form.protein_signal_score || 3) * 3 + (form.category_tags.length > 0 ? 5 : 0)) * 4);
  const cti = Math.min(100, (form.competitive_threat_score || 3) * 5 + 10);
  const pos = Math.min(100, (form.follow_up_flag === "deep_dive" ? 50 : form.follow_up_flag === "revisit" ? 35 : 20));
  const sps = Math.round(prs * 0.4 + cti * 0.35 + pos * 0.25);
  return { prs_score: prs, cti_score: cti, pos_score: pos, sps_score: sps, tier: sps >= 75 ? "tier1" : sps >= 50 ? "tier2" : "tier3", score_confidence: "medium" };
}

function previewDeep(form) {
  const prs = Math.min(100, ((form.strategic_fit_score || 3) * 3 + (form.claims_tags.length > 0 ? 4 : 0)) * 4);
  const cti = Math.min(100, (form.competitive_threat_score || 3) * 5 + (form.direct_competitor_flag ? 20 : 0) + (form.channel_presence.includes("Club") ? 15 : 0));
  const pos = Math.min(100, (form.partnership_potential_score || 3) * 5 + (form.manufacturing_type === "co_pack" ? 15 : 0) + (form.certifications.length * 4));
  const sps = Math.round(prs * 0.4 + cti * 0.35 + pos * 0.25);
  return { prs_score: prs, cti_score: cti, pos_score: pos, sps_score: sps, tier: sps >= 75 ? "tier1" : sps >= 50 ? "tier2" : "tier3", score_confidence: "high" };
}

export default App;

