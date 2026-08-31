import { AlertTriangle, ChevronDown, ChevronUp, Plus, RotateCcw, Swords, Trash2 } from "lucide-react";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { hpTone, MiniStatRow, PartyMemberBox } from "./PartyMemberBox.jsx";
import { Badge, InfoTooltip, NumberInput, Panel, Select, TextInput } from "./ui.jsx";
import { ThreatGauge } from "./ThreatGauge.jsx";

/** The special (non-baseline-attack) abilities a monster has, each with the
 * exact key the backend expects in item.monster_uses (must match how
 * compute_monster_profile names components) and a suggested default. */
function specialAbilitiesFor(monster, allSpells) {
  const out = [];
  for (const a of monster.save_attacks || []) {
    out.push({ key: a.name, label: a.name, defaultUses: a.default_uses_per_encounter ?? 1 });
  }
  for (const s of monster.spells || []) {
    const spell = allSpells[s.spell_id];
    if (!spell) continue;
    const key = `${spell.name} (innate)`;
    out.push({ key, label: key, defaultUses: s.default_uses_per_encounter ?? 1 });
  }
  if (monster.is_legendary) {
    for (const a of monster.legendary_actions || []) {
      const key = `${a.name} (legendary)`;
      out.push({ key, label: key, defaultUses: a.default_uses_per_encounter ?? 1 });
    }
  }
  return out;
}

export function EncounterCard({ item, party, bestiary, referenceData, customSpells, snap, onChange, onRemove, onMoveUp, onMoveDown }) {
  const [expandedParty, setExpandedParty] = useState({});
  const autoSuggested = useRef(false);
  const allSpells = useMemo(() => {
    const merged = { ...referenceData.spells };
    for (const s of customSpells || []) merged[s.id] = s;
    return merged;
  }, [referenceData.spells, customSpells]);

  const updateMonsterGroup = (i, patch) => onChange({ monsters: item.monsters.map((g, idx) => (idx === i ? { ...g, ...patch } : g)) });
  const addMonsterGroup = () => onChange({ monsters: [...item.monsters, { bestiary_id: bestiary[0]?.id, count: 1 }] });
  const removeMonsterGroup = (i) => onChange({ monsters: item.monsters.filter((_, idx) => idx !== i) });
  const setSpend = (charId, resName, val) => onChange({ spends: { ...item.spends, [charId]: { ...(item.spends[charId] || {}), [resName]: Math.max(0, val) } } });
  const setHpOverride = (charId, val) => onChange({ hp_overrides: { ...item.hp_overrides, [charId]: val } });
  const resetHpOverride = (charId) => {
    const next = { ...item.hp_overrides };
    delete next[charId];
    onChange({ hp_overrides: next });
  };
  const setMonsterUse = (bestiaryId, abilityKey, val) =>
    onChange({
      monster_uses: {
        ...item.monster_uses,
        [bestiaryId]: { ...(item.monster_uses?.[bestiaryId] || {}), [abilityKey]: Math.max(0, val) },
      },
    });

  const suggestSpend = () => {
    const spends = {};
    party.forEach((c) => {
      spends[c.id] = {};
      c.resources.forEach((r) => {
        const remaining = snap?.resources_before?.[c.id]?.[r.name] ?? r.max;
        const weight = snap?.label?.tone === "danger" ? 0.6 : snap?.label?.tone === "warn" ? 0.4 : 0.2;
        spends[c.id][r.name] = Math.round(remaining * weight);
      });
    });
    onChange({ spends });
  };

  // Resource spend is suggested automatically the first time this encounter
  // has a real result to suggest from - no button click needed. The button
  // that used to trigger this is now just a manual reset, for when you've
  // edited the numbers and want the suggestion back.
  useEffect(() => {
    if (autoSuggested.current) return;
    if (!snap) return;
    if (Object.keys(item.spends || {}).length > 0) {
      autoSuggested.current = true;
      return;
    }
    if (party.some((c) => c.resources.length > 0)) {
      suggestSpend();
    }
    autoSuggested.current = true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [snap]);

  if (!snap) return null;
  const tone = snap.label.tone;
  const borderColor = tone === "danger" ? "border-l-[#b3452c]" : tone === "warn" ? "border-l-[#c98a3a]" : "border-l-[#5c8a5c]";

  return (
    <Panel className={`p-4 border-l-4 ${borderColor}`}>
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-1 flex-wrap">
          <Swords size={16} className="text-[#c9a15a] shrink-0" />
          <TextInput value={item.name} onChange={(e) => onChange({ name: e.target.value })} className="max-w-xs" />
          <Badge tone={tone}>{snap.label.text}</Badge>
          <span className="text-[11px] text-[#8b93a7] font-mono2">
            {snap.total_xp.toLocaleString()} XP, budget {snap.budget.toLocaleString()}
          </span>
        </div>
        <div className="flex gap-1">
          <button onClick={onMoveUp} className="p-1.5 text-[#8b93a7] hover:text-[#e9e4d8]">
            <ChevronUp size={14} />
          </button>
          <button onClick={onMoveDown} className="p-1.5 text-[#8b93a7] hover:text-[#e9e4d8]">
            <ChevronDown size={14} />
          </button>
          <button onClick={onRemove} className="p-1.5 text-[#8b93a7] hover:text-[#b3452c]">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-4 mb-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#8b93a7] uppercase tracking-wide font-medium">Monster groups</span>
            <button onClick={addMonsterGroup} className="text-[10.5px] text-[#c9a15a] flex items-center gap-0.5">
              <Plus size={11} />
              add
            </button>
          </div>
          {item.monsters.map((g, i) => (
            <div key={i} className="flex gap-1.5 items-center">
              <Select value={g.bestiary_id} onChange={(e) => updateMonsterGroup(i, { bestiary_id: e.target.value })} className="!py-1 !text-xs">
                {bestiary.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                    {m.is_legendary ? " (Boss)" : ""}
                  </option>
                ))}
              </Select>
              <NumberInput value={g.count} min={1} onChange={(e) => updateMonsterGroup(i, { count: Math.max(1, +e.target.value || 1) })} className="!py-1 !text-xs w-16" />
              <button onClick={() => removeMonsterGroup(i)} className="text-[#5c6478] hover:text-[#b3452c] shrink-0">
                <Trash2 size={13} />
              </button>
            </div>
          ))}
          <div className="text-[10.5px] text-[#8b93a7] pt-1 space-y-0.5 font-mono2">
            <div>Fight length (computed, not a guess): ~{snap.rounds_assumed.toFixed(1)} rounds</div>
            <div>Monster HP pool: {snap.total_monster_hp}</div>
            <div>Monster dmg/round (post-armor): {snap.monster_dpr_total.toFixed(1)}</div>
            <div>Avg party AC: {snap.avg_party_ac.toFixed(0)}</div>
          </div>
          {snap.damage_mix_note && <p className="text-[10px] text-[#5c6478] pt-1 italic">{snap.damage_mix_note}</p>}
        </div>

        <div>
          <span className="text-xs text-[#8b93a7] uppercase tracking-wide font-medium block mb-2">Predicted difficulty</span>
          <ThreatGauge roundsToKillMonsters={snap.rounds_to_kill_monsters} roundsToDropPC={snap.rounds_to_drop_pc} roundsAssumed={snap.rounds_assumed} />
          {snap.warnings.map((w, i) => (
            <div key={i} className="flex items-start gap-1.5 mt-2 text-[11px] text-[#e0a860]">
              <AlertTriangle size={12} className="mt-0.5 shrink-0" />
              <span>{w}</span>
            </div>
          ))}
        </div>
      </div>

      {(() => {
        const uniqueBestiaryIds = [...new Set(item.monsters.map((g) => g.bestiary_id))];
        const groupsWithAbilities = uniqueBestiaryIds
          .map((id) => bestiary.find((m) => m.id === id))
          .filter(Boolean)
          .map((m) => ({ monster: m, abilities: specialAbilitiesFor(m, allSpells) }))
          .filter((g) => g.abilities.length > 0);
        if (groupsWithAbilities.length === 0) return null;
        return (
          <div className="mb-4">
            <span className="text-xs text-[#8b93a7] uppercase tracking-wide font-medium flex items-center gap-1 mb-2">
              Special abilities this fight
              <InfoTooltip text="How many times each ability actually fires in THIS encounter - a plain total, not a per-round rate. 'I expect the dragon to breathe fire once this fight' is entered as 1. Defaults to the Bestiary's suggested typical uses; editing it here only affects this one encounter." />
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {groupsWithAbilities.map(({ monster, abilities }) => (
                <div key={monster.id} className="bg-[#141821] rounded-sm p-3 border border-[#333c52]">
                  <div className="text-xs font-medium text-[#c7cbd6] mb-1.5">{monster.name}</div>
                  <div className="space-y-1">
                    {abilities.map((a) => {
                      const value = item.monster_uses?.[monster.id]?.[a.key] ?? a.defaultUses;
                      return (
                        <div key={a.key} className="flex items-center gap-1.5">
                          <span className="flex-1 truncate text-[10.5px] text-[#8b93a7]" title={a.label}>
                            {a.label}
                          </span>
                          <NumberInput
                            value={value}
                            min={0}
                            onChange={(e) => setMonsterUse(monster.id, a.key, +e.target.value || 0)}
                            className="!py-0.5 !text-[10.5px] w-14"
                          />
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })()}

      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-[#8b93a7] uppercase tracking-wide font-medium">Party</span>
          <button onClick={suggestSpend} className="text-[10.5px] text-[#8b93a7] hover:text-[#c9a15a] flex items-center gap-1">
            <RotateCcw size={11} />
            reset to suggested spend
          </button>
        </div>
        <div className="flex flex-wrap gap-2 items-start">
          {party.map((c) => {
            const hpBefore = snap.hp_before[c.id];
            const predicted = snap.predicted_hp_after[c.id];
            const hasOverride = Object.prototype.hasOwnProperty.call(item.hp_overrides || {}, c.id);
            const hpAfter = hasOverride ? item.hp_overrides[c.id] : predicted;
            return (
              <PartyMemberBox
                key={c.id}
                character={c}
                expanded={!!expandedParty[c.id]}
                onToggle={() => setExpandedParty((s) => ({ ...s, [c.id]: !s[c.id] }))}
                statusLine={`${hpBefore}\u2192${hpAfter}/${c.max_hp}`}
                statusTone={hpTone(hpAfter, c.max_hp)}
              >
                <div className="text-[#8b93a7]">
                  Entering: {hpBefore}/{c.max_hp} HP
                </div>
                {c.resources.map((r) => {
                  const remaining = snap.resources_before[c.id]?.[r.name] ?? r.max;
                  const spent = item.spends[c.id]?.[r.name] || 0;
                  return (
                    <MiniStatRow
                      key={r.name}
                      label={r.name}
                      secondary={`${remaining} left`}
                      value={spent}
                      max={remaining}
                      onChange={(e) => setSpend(c.id, r.name, Math.min(remaining, +e.target.value || 0))}
                    />
                  );
                })}
                <div className="flex items-center gap-1 pt-1 border-t border-[#333c52]">
                  <span className="flex-1 text-[#8b93a7]">HP after</span>
                  <span className="font-mono2 text-[#5c6478] text-[9px]">/{c.max_hp}</span>
                  <NumberInput
                    value={hpAfter}
                    min={0}
                    max={c.max_hp}
                    onChange={(e) => setHpOverride(c.id, Math.max(0, Math.min(c.max_hp, +e.target.value || 0)))}
                    className={`!py-0.5 !text-[10.5px] w-12 ${hasOverride ? "!border-[#c9a15a]/50" : ""}`}
                  />
                  {hasOverride && (
                    <button onClick={() => resetHpOverride(c.id)} title="Reset to predicted" className="text-[#5c6478] hover:text-[#c9a15a]">
                      <RotateCcw size={11} />
                    </button>
                  )}
                </div>
              </PartyMemberBox>
            );
          })}
        </div>
        <p className="text-[10px] text-[#5c6478] mt-2 leading-snug">
          Resource spend is suggested automatically; edit any number by hand. HP after is auto-filled with the
          predicted value. Edit it if the table played out differently; that edited value is what carries into the
          next encounter, not the prediction.
        </p>
      </div>
    </Panel>
  );
}
