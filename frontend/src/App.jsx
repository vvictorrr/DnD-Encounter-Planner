import { BookOpen, FolderOpen, Info, Save, ScrollText, Skull, Swords, Users } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { api } from "./api/client.js";
import { AnalysisTab } from "./components/AnalysisTab.jsx";
import { BestiaryTab } from "./components/BestiaryTab.jsx";
import { DayTab } from "./components/DayTab.jsx";
import { GuideTab } from "./components/GuideTab.jsx";
import { PartyTab } from "./components/PartyTab.jsx";
import { SpellLibraryTab } from "./components/SpellLibraryTab.jsx";
import { TextInput } from "./components/ui.jsx";
import { newCharacter, newMonster } from "./utils/factories.js";

const TABS = [
  { id: "party", label: "Party", icon: Users },
  { id: "spells", label: "Spell Library", icon: BookOpen },
  { id: "bestiary", label: "Bestiary", icon: Skull },
  { id: "day", label: "Adventuring Day", icon: Swords },
  { id: "analysis", label: "Analysis", icon: FolderOpen },
  { id: "guide", label: "How this works", icon: Info },
];

export default function App() {
  const [referenceData, setReferenceData] = useState(null);
  const [party, setParty] = useState([newCharacter()]);
  const [bestiary, setBestiary] = useState([newMonster()]);
  const [customSpells, setCustomSpells] = useState([]);
  const [items, setItems] = useState([]);
  // Starting conditions for the day: sparse, keyed by character id. A
  // character with no entry here just starts at their own max HP/resources.
  const [startingHp, setStartingHp] = useState({});
  const [startingResources, setStartingResources] = useState({});
  const [tab, setTab] = useState("party");

  const [campaignId, setCampaignId] = useState(null);
  const [campaignName, setCampaignName] = useState("Untitled Campaign");
  const [campaignList, setCampaignList] = useState([]);
  const [saveMsg, setSaveMsg] = useState("");

  const [snapshots, setSnapshots] = useState([]);
  const [simError, setSimError] = useState(null);

  // Reference data (class list, subclasses, feats, spells, ...) loads once.
  useEffect(() => {
    api.getReferenceData().then(setReferenceData).catch((e) => setSimError(e.message));
    api.listCampaigns().then(setCampaignList).catch(() => {});
  }, []);

  // Every change to the party/bestiary/day plan re-runs the simulation
  // through the real backend engine, debounced so typing doesn't spam it.
  useEffect(() => {
    if (items.length === 0) {
      setSnapshots([]);
      return;
    }
    const handle = setTimeout(() => {
      api
        .simulate(party, bestiary, items, customSpells, startingHp, startingResources)
        .then((res) => {
          setSnapshots(res.snapshots);
          setSimError(null);
        })
        .catch((e) => setSimError(e.message));
    }, 300);
    return () => clearTimeout(handle);
  }, [party, bestiary, items, customSpells, startingHp, startingResources]);

  const saveCampaign = async () => {
    const data = {
      name: campaignName, party, bestiary, day_plan: items,
      custom_spells: customSpells, starting_hp: startingHp, starting_resources: startingResources,
    };
    const saved = campaignId ? await api.updateCampaign(campaignId, data) : await api.createCampaign(data);
    setCampaignId(saved.id);
    setSaveMsg("Saved");
    setTimeout(() => setSaveMsg(""), 1500);
    api.listCampaigns().then(setCampaignList).catch(() => {});
  };

  const loadCampaign = async (id) => {
    if (!id) return;
    const c = await api.getCampaign(id);
    setCampaignId(c.id);
    setCampaignName(c.name);
    setParty(c.party.length ? c.party : [newCharacter()]);
    setBestiary(c.bestiary.length ? c.bestiary : [newMonster()]);
    setCustomSpells(c.custom_spells || []);
    setStartingHp(c.starting_hp || {});
    setStartingResources(c.starting_resources || {});
    setItems(c.day_plan);
  };

  if (!referenceData) {
    return <div className="min-h-screen bg-[#14171f] text-[#8b93a7] p-8">Loading reference data from the backend.</div>;
  }

  return (
    <div className="min-h-screen bg-[#14171f] text-[#e9e4d8]">
      <header className="border-b border-[#333c52] px-6 py-4 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-sm bg-[#c9a15a]/15 border border-[#c9a15a]/40 flex items-center justify-center">
            <ScrollText size={18} className="text-[#c9a15a]" />
          </div>
          <div>
            <h1 className="font-display text-xl font-bold tracking-tight text-[#e9e4d8]">DnD Encounter Planner</h1>
            <p className="text-[10.5px] text-[#8b93a7] -mt-0.5">2014 rules</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <TextInput value={campaignName} onChange={(e) => setCampaignName(e.target.value)} className="!w-48" />
          <select
            className="bg-[#1c212e] border border-[#333c52] rounded-sm px-2 py-1.5 text-xs text-[#8b93a7]"
            onChange={(e) => loadCampaign(e.target.value ? Number(e.target.value) : null)}
            value=""
          >
            <option value="">Load campaign...</option>
            {campaignList.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <button onClick={saveCampaign} className="flex items-center gap-1.5 bg-[#242b3d] hover:bg-[#2c3446] border border-[#333c52] rounded-sm px-3 py-1.5 text-xs font-medium">
            <Save size={13} /> {saveMsg || "Save campaign"}
          </button>
        </div>
      </header>

      <nav className="border-b border-[#333c52] px-6 flex gap-1 overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors whitespace-nowrap ${
              tab === t.id ? "border-[#c9a15a] text-[#e9e4d8]" : "border-transparent text-[#8b93a7] hover:text-[#c7cbd6]"
            }`}
          >
            <t.icon size={14} />
            {t.label}
          </button>
        ))}
      </nav>

      <main className="p-6 max-w-[1280px] w-full mx-auto overflow-x-hidden">
        {tab === "party" && <PartyTab party={party} setParty={setParty} referenceData={referenceData} customSpells={customSpells} />}
        {tab === "spells" && <SpellLibraryTab customSpells={customSpells} setCustomSpells={setCustomSpells} referenceData={referenceData} />}
        {tab === "bestiary" && <BestiaryTab bestiary={bestiary} setBestiary={setBestiary} referenceData={referenceData} customSpells={customSpells} />}
        {tab === "day" && (
          <DayTab
            party={party} bestiary={bestiary} items={items} setItems={setItems}
            referenceData={referenceData} customSpells={customSpells} snapshots={snapshots} simError={simError}
            startingHp={startingHp} setStartingHp={setStartingHp}
            startingResources={startingResources} setStartingResources={setStartingResources}
          />
        )}
        {tab === "analysis" && <AnalysisTab party={party} items={items} snapshots={snapshots} />}
        {tab === "guide" && <GuideTab />}
      </main>
    </div>
  );
}
