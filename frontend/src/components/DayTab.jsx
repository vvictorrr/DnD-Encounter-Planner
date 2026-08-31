import { AlertTriangle, ChevronDown, ChevronUp, Coffee, Moon, Plus, RotateCcw, Trash2 } from "lucide-react";
import React, { useState } from "react";
import { newEncounter, newRest } from "../utils/factories.js";
import { EncounterCard } from "./EncounterCard.jsx";
import { hpTone, MiniStatRow, PartyMemberBox } from "./PartyMemberBox.jsx";
import { NumberInput, Panel } from "./ui.jsx";

function StartingConditionsRow({ party, startingHp, setStartingHp, startingResources, setStartingResources }) {
  const [expandedChar, setExpandedChar] = useState({});

  const setHp = (charId, val) => setStartingHp((prev) => ({ ...prev, [charId]: val }));
  const setResource = (charId, resName, val) =>
    setStartingResources((prev) => ({ ...prev, [charId]: { ...(prev[charId] || {}), [resName]: val } }));
  const resetChar = (charId) => {
    setStartingHp((prev) => {
      const next = { ...prev };
      delete next[charId];
      return next;
    });
    setStartingResources((prev) => {
      const next = { ...prev };
      delete next[charId];
      return next;
    });
  };

  return (
    <Panel className="p-4">
      <span className="text-sm font-medium text-[#e9e4d8] block mb-1">Starting conditions</span>
      <p className="text-[11px] text-[#8b93a7] mb-3">
        Picking up mid-adventure? Set what the party actually has left before the first encounter. Leave a field
        alone and it defaults to full.
      </p>
      <div className="flex flex-wrap gap-2 items-start">
        {party.map((c) => {
          const hp = startingHp[c.id] ?? c.max_hp;
          return (
            <PartyMemberBox
              key={c.id}
              character={c}
              expanded={!!expandedChar[c.id]}
              onToggle={() => setExpandedChar((s) => ({ ...s, [c.id]: !s[c.id] }))}
              statusLine={`${hp}/${c.max_hp} HP`}
              statusTone={hpTone(hp, c.max_hp)}
            >
              <MiniStatRow label="HP" secondary={`/${c.max_hp}`} value={hp} onChange={(e) => setHp(c.id, +e.target.value || 0)} />
              {c.resources.map((r) => (
                <MiniStatRow
                  key={r.name}
                  label={r.name}
                  secondary={`/${r.max}`}
                  value={startingResources[c.id]?.[r.name] ?? r.max}
                  max={r.max}
                  onChange={(e) => setResource(c.id, r.name, Math.max(0, Math.min(r.max, +e.target.value || 0)))}
                />
              ))}
              <button onClick={() => resetChar(c.id)} className="flex items-center gap-1 text-[#5c6478] hover:text-[#c9a15a] pt-1 border-t border-[#333c52] w-full">
                <RotateCcw size={11} /> reset to full
              </button>
            </PartyMemberBox>
          );
        })}
      </div>
    </Panel>
  );
}

function RestRow({ item, party, hpEntering, onChange, onRemove, onMoveUp, onMoveDown }) {
  const [expanded, setExpanded] = useState(false);
  const isLong = item.rest_type === "long";
  const setHeal = (charId, val) => onChange({ heals: { ...item.heals, [charId]: Math.max(0, val) } });

  return (
    <Panel className={`p-3 border-l-4 ${isLong ? "border-l-[#7a8fc9]" : "border-l-[#8fbf8f]"}`}>
      <div className="flex items-center justify-between">
        <button onClick={() => !isLong && setExpanded((x) => !x)} className="flex items-center gap-2 text-sm font-medium text-left">
          {isLong ? <Moon size={15} className="text-[#7a8fc9]" /> : <Coffee size={15} className="text-[#8fbf8f]" />}
          {isLong ? "Long Rest" : "Short Rest"}
          <span className="text-[11px] text-[#8b93a7] font-normal">
            {isLong ? "Full HP restore, all resources reset." : "Short-rest resources restored. Add any Hit Dice/healing spent below."}
          </span>
          {!isLong && (expanded ? <ChevronUp size={12} className="text-[#8b93a7]" /> : <ChevronDown size={12} className="text-[#8b93a7]" />)}
        </button>
        <div className="flex gap-1">
          <button onClick={onMoveUp} className="p-1 text-[#8b93a7] hover:text-[#e9e4d8]">
            <ChevronUp size={14} />
          </button>
          <button onClick={onMoveDown} className="p-1 text-[#8b93a7] hover:text-[#e9e4d8]">
            <ChevronDown size={14} />
          </button>
          <button onClick={onRemove} className="p-1 text-[#8b93a7] hover:text-[#b3452c]">
            <Trash2 size={14} />
          </button>
        </div>
      </div>
      {!isLong && expanded && (
        <div className="flex flex-wrap gap-2 items-start mt-3">
          {party.map((c) => {
            const before = hpEntering[c.id] ?? c.max_hp;
            const healed = item.heals?.[c.id] || 0;
            const after = Math.min(c.max_hp, before + healed);
            return (
              <div key={c.id} className="w-28 shrink-0 bg-[#141821] border border-[#333c52] rounded-sm p-2 text-[10.5px] space-y-1">
                <div className="text-[#c7cbd6] truncate">{c.name}</div>
                <div className={`font-mono2 ${hpTone(after, c.max_hp)}`}>
                  {before}→{after}/{c.max_hp}
                </div>
                <div className="flex items-center gap-1">
                  <span className="flex-1 text-[#8b93a7]">healed</span>
                  <NumberInput
                    value={healed}
                    min={0}
                    onChange={(e) => setHeal(c.id, +e.target.value || 0)}
                    className="!py-0.5 !text-[10.5px] w-12"
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Panel>
  );
}

export function DayTab({
  party, bestiary, items, setItems, referenceData, customSpells, snapshots, simError,
  startingHp, setStartingHp, startingResources, setStartingResources,
}) {
  const addEncounter = () => setItems((it) => [...it, newEncounter(bestiary)]);
  const addRest = (kind) => setItems((it) => [...it, newRest(kind)]);
  const removeItem = (id) => setItems((it) => it.filter((x) => x.id !== id));
  const updateItem = (id, patch) => setItems((it) => it.map((x) => (x.id === id ? { ...x, ...patch } : x)));
  const move = (id, dir) =>
    setItems((it) => {
      const idx = it.findIndex((x) => x.id === id);
      const j = idx + dir;
      if (j < 0 || j >= it.length) return it;
      const copy = [...it];
      [copy[idx], copy[j]] = [copy[j], copy[idx]];
      return copy;
    });

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <p className="text-sm text-[#8b93a7] max-w-2xl">
          Lay out the day in order, pulling monster groups from your Bestiary. Each encounter carries forward whatever HP and resources
          survived the last one, and damage math runs through each monster's real resistance profile rather than a flat number.
        </p>
        <div className="flex gap-2">
          <button onClick={() => addRest("short")} className="flex items-center gap-1.5 bg-[#242b3d] border border-[#333c52] rounded-sm px-3 py-2 text-xs font-medium hover:bg-[#2c3446]">
            <Coffee size={13} /> Short rest
          </button>
          <button onClick={() => addRest("long")} className="flex items-center gap-1.5 bg-[#242b3d] border border-[#333c52] rounded-sm px-3 py-2 text-xs font-medium hover:bg-[#2c3446]">
            <Moon size={13} /> Long rest
          </button>
          <button
            onClick={addEncounter}
            disabled={bestiary.length === 0}
            className="flex items-center gap-1.5 bg-[#c9a15a] disabled:opacity-40 text-[#14171f] font-semibold rounded-sm px-3 py-2 text-sm hover:bg-[#d8b06c]"
          >
            <Plus size={15} /> Encounter
          </button>
        </div>
      </div>

      {bestiary.length === 0 && (
        <Panel className="p-4 text-sm text-[#e0a860] flex items-center gap-2">
          <AlertTriangle size={15} />
          Add at least one monster in the Bestiary tab before building encounters.
        </Panel>
      )}
      {simError && (
        <Panel className="p-4 text-sm text-[#e08065] flex items-center gap-2">
          <AlertTriangle size={15} />
          Simulation error: {simError}
        </Panel>
      )}

      <StartingConditionsRow
        party={party} startingHp={startingHp} setStartingHp={setStartingHp}
        startingResources={startingResources} setStartingResources={setStartingResources}
      />

      {items.length === 0 && bestiary.length > 0 && <Panel className="p-8 text-center text-[#8b93a7] text-sm">No encounters yet. Add one to start planning the day.</Panel>}

      <div className="space-y-4">
        {items.map((item, idx) => {
          const snap = snapshots[idx];
          if (item.type === "rest") {
            // HP entering this rest = the last encounter's actual outcome
            // before it, or the day's starting HP if nothing came before.
            let hpEntering = null;
            for (let i = idx - 1; i >= 0; i--) {
              if (snapshots[i]) {
                hpEntering = snapshots[i].hp_after;
                break;
              }
            }
            if (!hpEntering) {
              hpEntering = Object.fromEntries(party.map((c) => [c.id, startingHp[c.id] ?? c.max_hp]));
            }
            return (
              <RestRow
                key={item.id}
                item={item}
                party={party}
                hpEntering={hpEntering}
                onChange={(patch) => updateItem(item.id, patch)}
                onRemove={() => removeItem(item.id)}
                onMoveUp={() => move(item.id, -1)}
                onMoveDown={() => move(item.id, 1)}
              />
            );
          }
          return (
            <EncounterCard
              key={item.id}
              item={item}
              party={party}
              bestiary={bestiary}
              referenceData={referenceData}
              customSpells={customSpells}
              snap={snap}
              onChange={(patch) => updateItem(item.id, patch)}
              onRemove={() => removeItem(item.id)}
              onMoveUp={() => move(item.id, -1)}
              onMoveDown={() => move(item.id, 1)}
            />
          );
        })}
      </div>
    </div>
  );
}
