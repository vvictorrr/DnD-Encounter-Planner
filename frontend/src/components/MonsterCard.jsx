import { ChevronDown, ChevronUp, Crown, Plus, Sparkles, Trash2 } from "lucide-react";
import React, { useMemo, useState } from "react";
import { api } from "../api/client.js";
import { ABILITIES, newAttack, newLegendaryAction, newMonsterSpell, newSaveAttack } from "../utils/factories.js";
import { expectedAttackDamage } from "../utils/spellMath.js";
import { DamageTypeListEditor, Field, InfoTooltip, NumberInput, Panel, Select, StatCardRow, TextInput } from "./ui.jsx";

function referenceDpr(m) {
  return (m.attacks || []).reduce(
    (sum, a) => sum + expectedAttackDamage(a.count, a.to_hit, 15, a.die_count, a.die_sides, a.flat_bonus), 0,
  );
}

/** A labeled mini-field for a dense attack-row grid: a tiny caption above a
 * small control. Every attack/save-attack/legendary-action row is built out
 * of these, always at col-span-1. */
function MiniField({ label, children }) {
  return (
    <div className="col-span-1 flex flex-col items-center min-w-0">
      <span className="text-[8px] text-[#5c6478]">{label}</span>
      {children}
    </div>
  );
}

/** The "dmg dice / die sides / flat dmg" trio every damage-dealing row needs
 * (attacks, save-attacks, legendary actions all use the exact same three
 * fields), so it's written once instead of three times per row type. */
function DamageDiceFields({ item, onUpdate }) {
  return (
    <>
      <MiniField label="dmg dice">
        <NumberInput value={item.die_count} onChange={(e) => onUpdate({ die_count: +e.target.value || 1 })} className="!py-0.5 !text-xs" />
      </MiniField>
      <MiniField label="die sides">
        <NumberInput value={item.die_sides} onChange={(e) => onUpdate({ die_sides: +e.target.value || 6 })} className="!py-0.5 !text-xs" />
      </MiniField>
      <MiniField label="flat dmg">
        <NumberInput value={item.flat_bonus} onChange={(e) => onUpdate({ flat_bonus: +e.target.value || 0 })} className="!py-0.5 !text-xs" />
      </MiniField>
    </>
  );
}

const ABILITY_LABELS = { str: "STR", dex: "DEX", con: "CON", int: "INT", wis: "WIS", cha: "CHA" };

export function MonsterCard({ m, referenceData, customSpells, onChange, onRemove }) {
  const [expanded, setExpanded] = useState(true);
  const [seedCr, setSeedCr] = useState("5");
  const dpr = useMemo(() => referenceDpr(m), [m]);

  const updateAttack = (i, patch) => onChange({ attacks: m.attacks.map((a, idx) => (idx === i ? { ...a, ...patch } : a)) });
  const removeAttack = (i) => onChange({ attacks: m.attacks.filter((_, idx) => idx !== i) });
  const updateSaveAttack = (i, patch) => onChange({ save_attacks: m.save_attacks.map((a, idx) => (idx === i ? { ...a, ...patch } : a)) });
  const removeSaveAttack = (i) => onChange({ save_attacks: m.save_attacks.filter((_, idx) => idx !== i) });
  const updateLegendary = (i, patch) => onChange({ legendary_actions: m.legendary_actions.map((a, idx) => (idx === i ? { ...a, ...patch } : a)) });
  const removeLegendary = (i) => onChange({ legendary_actions: m.legendary_actions.filter((_, idx) => idx !== i) });
  const updateSpell = (i, patch) => onChange({ spells: m.spells.map((s, idx) => (idx === i ? { ...s, ...patch } : s)) });
  const removeSpell = (i) => onChange({ spells: m.spells.filter((_, idx) => idx !== i) });
  const allSpells = useMemo(() => {
    const merged = { ...referenceData.spells };
    for (const s of customSpells) merged[s.id] = s;
    return merged;
  }, [referenceData.spells, customSpells]);

  const seedFromCr = async () => {
    const { seed } = await api.getMonsterSeed(seedCr);
    onChange(seed);
  };

  return (
    <Panel className={`p-4 border-l-4 ${m.is_legendary ? "border-l-[#c9a15a]" : "border-l-transparent"}`}>
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 flex gap-2">
          <TextInput value={m.name} onChange={(e) => onChange({ name: e.target.value })} />
          <label className="flex items-center gap-1.5 text-xs text-[#c7cbd6] whitespace-nowrap px-2 bg-[#141821] border border-[#333c52] rounded-sm">
            <input type="checkbox" checked={m.is_legendary} onChange={(e) => onChange({ is_legendary: e.target.checked })} className="accent-[#c9a15a]" />
            <Crown size={12} className={m.is_legendary ? "text-[#c9a15a]" : "text-[#5c6478]"} /> Boss
          </label>
        </div>
        <div className="flex gap-1">
          <button onClick={() => setExpanded((x) => !x)} className="p-1.5 text-[#8b93a7] hover:text-[#e9e4d8]">
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          <button onClick={onRemove} className="p-1.5 text-[#8b93a7] hover:text-[#b3452c]">
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      <div className="flex gap-2 items-center mb-3">
        <Select value={seedCr} onChange={(e) => setSeedCr(e.target.value)} className="!py-1 !text-xs w-28">
          {referenceData.cr_order.map((cr) => (
            <option key={cr} value={cr}>
              CR {cr}
            </option>
          ))}
        </Select>
        <button onClick={seedFromCr} className="text-[10.5px] text-[#8b93a7] hover:text-[#c9a15a] underline">
          seed a ballpark stat block (optional, fully editable after)
        </button>
      </div>

      <StatCardRow
        stats={[
          { label: "Attack DPR @ AC15 (excl. saves/spells)", value: dpr.toFixed(1), accent: true },
          { label: "HP", value: m.max_hp },
          { label: "AC", value: m.ac },
        ]}
      />

      {expanded && (
        <div className="mt-4 space-y-4">
          <div className="grid grid-cols-3 gap-2">
            <Field label="AC">
              <NumberInput value={m.ac} onChange={(e) => onChange({ ac: +e.target.value || 0 })} />
            </Field>
            <Field label="Max HP">
              <NumberInput value={m.max_hp} onChange={(e) => onChange({ max_hp: +e.target.value || 1 })} />
            </Field>
            <Field label="XP (for budget calc)">
              <NumberInput value={m.xp} onChange={(e) => onChange({ xp: +e.target.value || 0 })} />
            </Field>
          </div>

          <div>
            <span className="text-[10.5px] text-[#8b93a7] uppercase tracking-wide font-medium block mb-1">
              Saving throw bonuses
            </span>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
              {ABILITIES.map((a) => (
                <div key={a} className="bg-[#141821] rounded-sm px-2 py-1 border border-[#333c52]">
                  <span className="text-[9px] text-[#5c6478] uppercase">{ABILITY_LABELS[a]}</span>
                  <NumberInput
                    value={m.save_bonuses?.[a] ?? 0}
                    onChange={(e) => onChange({ save_bonuses: { ...m.save_bonuses, [a]: +e.target.value || 0 } })}
                    className="!py-0.5 !text-xs"
                  />
                </div>
              ))}
            </div>
            <p className="text-[10px] text-[#5c6478] mt-1 italic">
              Used when a character's spell or ability calls for a specific save - a Fireball checks this monster's
              Dex bonus, not a single flat number for every kind of save.
            </p>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs text-[#8b93a7] uppercase tracking-wide font-medium flex items-center gap-1">
                Attacks (to-hit based)
                <InfoTooltip text="One attack routine: # = how many times it repeats per turn. to hit = attack bonus vs AC. dmg dice/die sides = the damage die (e.g. 2 and 8 = 2d8). flat dmg = flat bonus added on top, same as a character's weapon stats on the Party page." />
              </span>
              <button onClick={() => onChange({ attacks: [...m.attacks, newAttack()] })} className="text-[10.5px] text-[#c9a15a] flex items-center gap-0.5">
                <Plus size={11} />
                add
              </button>
            </div>
            <div className="space-y-1.5">
              {m.attacks.map((a, i) => (
                <div key={a.id} className="grid grid-cols-12 gap-1 items-center bg-[#141821] rounded-sm px-2 py-1.5 border border-[#333c52]">
                  <input className="col-span-3 bg-transparent text-xs focus:outline-none" value={a.name} onChange={(e) => updateAttack(i, { name: e.target.value })} />
                  <MiniField label="#">
                    <NumberInput value={a.count} onChange={(e) => updateAttack(i, { count: +e.target.value || 1 })} className="!py-0.5 !text-xs" />
                  </MiniField>
                  <MiniField label="to hit">
                    <NumberInput value={a.to_hit} onChange={(e) => updateAttack(i, { to_hit: +e.target.value || 0 })} className="!py-0.5 !text-xs" />
                  </MiniField>
                  <DamageDiceFields item={a} onUpdate={(patch) => updateAttack(i, patch)} />
                  <Select value={a.damage_type} onChange={(e) => updateAttack(i, { damage_type: e.target.value })} className="col-span-2 !py-0.5 !text-[10px]">
                    {referenceData.damage_types.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </Select>
                  <MiniField label="magic">
                    <input type="checkbox" checked={!!a.magical} onChange={(e) => updateAttack(i, { magical: e.target.checked })} className="accent-[#c9a15a]" />
                  </MiniField>
                  <button onClick={() => removeAttack(i)} className="col-span-1 text-[#5c6478] hover:text-[#b3452c] flex justify-center">
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs text-[#8b93a7] uppercase tracking-wide font-medium flex items-center gap-1">
                Save-based attacks (breath weapons, AoEs)
                <InfoTooltip text="save = which ability the target rolls. DC = save DC. dmg dice/die sides + flat dmg work like a normal attack's damage. 'magic' = counts as magical for resistances. 'half dmg' = target still takes half damage on a successful save; leave unchecked if a success means no damage at all. Typical uses is a suggested default (per-encounter, not per-round) that pre-fills when you add this monster to a fight - the real expected uses for a given encounter is set per-encounter in the Adventuring Day tab, since a recharge ability might realistically fire once in a short fight and twice in a long one." />
              </span>
              <button onClick={() => onChange({ save_attacks: [...m.save_attacks, newSaveAttack()] })} className="text-[10.5px] text-[#c9a15a] flex items-center gap-0.5">
                <Plus size={11} />
                add
              </button>
            </div>
            <div className="space-y-1.5">
              {m.save_attacks.map((a, i) => (
                <div key={a.id} className="grid grid-cols-[repeat(15,minmax(0,1fr))] gap-1 items-center bg-[#141821] rounded-sm px-2 py-1.5 border border-[#333c52]">
                  <input className="col-span-3 bg-transparent text-xs focus:outline-none" value={a.name} onChange={(e) => updateSaveAttack(i, { name: e.target.value })} />
                  <MiniField label="typical uses">
                    <NumberInput value={a.default_uses_per_encounter} onChange={(e) => updateSaveAttack(i, { default_uses_per_encounter: +e.target.value || 0 })} className="!py-0.5 !text-xs" />
                  </MiniField>
                  <MiniField label="save">
                    <Select value={a.save_ability || "dex"} onChange={(e) => updateSaveAttack(i, { save_ability: e.target.value })} className="!py-0.5 !text-[9px]">
                      {ABILITIES.map((ab) => (
                        <option key={ab} value={ab}>
                          {ABILITY_LABELS[ab]}
                        </option>
                      ))}
                    </Select>
                  </MiniField>
                  <MiniField label="DC">
                    <NumberInput value={a.dc} onChange={(e) => updateSaveAttack(i, { dc: +e.target.value || 0 })} className="!py-0.5 !text-xs" />
                  </MiniField>
                  <DamageDiceFields item={a} onUpdate={(patch) => updateSaveAttack(i, patch)} />
                  <Select value={a.damage_type} onChange={(e) => updateSaveAttack(i, { damage_type: e.target.value })} className="col-span-2 !py-0.5 !text-[10px]">
                    {referenceData.damage_types.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </Select>
                  <MiniField label="magic">
                    <input type="checkbox" checked={!!a.magical} onChange={(e) => updateSaveAttack(i, { magical: e.target.checked })} className="accent-[#c9a15a]" />
                  </MiniField>
                  <MiniField label="half dmg">
                    <input type="checkbox" checked={!!a.half_on_save} onChange={(e) => updateSaveAttack(i, { half_on_save: e.target.checked })} className="accent-[#c9a15a]" />
                  </MiniField>
                  <button onClick={() => removeSaveAttack(i)} className="col-span-1 text-[#5c6478] hover:text-[#b3452c] flex justify-center">
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
              {m.save_attacks.length === 0 && <p className="text-[11px] text-[#5c6478] italic">None yet.</p>}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs text-[#8b93a7] uppercase tracking-wide font-medium flex items-center gap-1.5">
                <Sparkles size={13} className="text-[#c9a15a]" />
                Innate spellcasting
                <InfoTooltip text="Typical uses is a suggested default that pre-fills when you add this monster to an encounter, not what actually gets used - the real expected uses for a given fight is set per-encounter in the Adventuring Day tab, since it can reasonably vary fight to fight." />
              </span>
              <button onClick={() => onChange({ spells: [...m.spells, newMonsterSpell()] })} className="text-[10.5px] text-[#c9a15a] flex items-center gap-0.5">
                <Plus size={11} />
                add
              </button>
            </div>
            <div className="space-y-1.5">
              {m.spells.map((s, i) => {
                const spellData = allSpells[s.spell_id];
                return (
                  <div key={s.id} className="grid grid-cols-12 gap-1 items-center bg-[#141821] rounded-sm px-2 py-1.5 border border-[#333c52]">
                    <Select value={s.spell_id} onChange={(e) => updateSpell(i, { spell_id: e.target.value })} className="col-span-4 !py-0.5 !text-[10.5px]">
                      {Object.entries(allSpells).map(([id, spell]) => (
                        <option key={id} value={id}>
                          {spell.name} {spell.level === 0 ? "(cantrip)" : `(Lv${spell.level})`}
                        </option>
                      ))}
                    </Select>
                    <div className="col-span-2 flex flex-col items-center">
                      <span className="text-[8px] text-[#5c6478]">typical uses</span>
                      <NumberInput value={s.default_uses_per_encounter} onChange={(e) => updateSpell(i, { default_uses_per_encounter: +e.target.value || 0 })} className="!py-0.5 !text-xs" />
                    </div>
                    {spellData?.mode === "save" ? (
                      <div className="col-span-2 flex flex-col items-center">
                        <span className="text-[8px] text-[#5c6478]">save DC</span>
                        <NumberInput value={s.spell_save_dc} onChange={(e) => updateSpell(i, { spell_save_dc: +e.target.value || 0 })} className="!py-0.5 !text-xs" />
                      </div>
                    ) : (
                      <div className="col-span-2 flex flex-col items-center">
                        <span className="text-[8px] text-[#5c6478]">to hit</span>
                        <NumberInput value={s.spell_attack_bonus} onChange={(e) => updateSpell(i, { spell_attack_bonus: +e.target.value || 0 })} className="!py-0.5 !text-xs" />
                      </div>
                    )}
                    <div className="col-span-3 text-[10px] text-[#5c6478] truncate">
                      {spellData ? `${spellData.damage_type} · ${spellData.mode}${spellData.save_ability ? ` (${spellData.save_ability})` : ""}` : ""}
                    </div>
                    <button onClick={() => removeSpell(i)} className="col-span-1 text-[#5c6478] hover:text-[#b3452c] flex justify-center">
                      <Trash2 size={13} />
                    </button>
                  </div>
                );
              })}
              {m.spells.length === 0 && <p className="text-[11px] text-[#5c6478] italic">None. Draws on the same spell list characters use - real damage math, not a flat number.</p>}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <span className="text-[10.5px] text-[#8b93a7] uppercase tracking-wide font-medium block mb-1">Resistances</span>
              <DamageTypeListEditor list={m.resistances} onChange={(l) => onChange({ resistances: l })} damageTypes={referenceData.damage_types} tone="good" />
            </div>
            <div>
              <span className="text-[10.5px] text-[#8b93a7] uppercase tracking-wide font-medium block mb-1">Vulnerabilities</span>
              <DamageTypeListEditor list={m.vulnerabilities} onChange={(l) => onChange({ vulnerabilities: l })} damageTypes={referenceData.damage_types} tone="danger" />
            </div>
            <div>
              <span className="text-[10.5px] text-[#8b93a7] uppercase tracking-wide font-medium block mb-1">Immunities</span>
              <DamageTypeListEditor list={m.immunities} onChange={(l) => onChange({ immunities: l })} damageTypes={referenceData.damage_types} tone="neutral" />
            </div>
          </div>

          {m.is_legendary && (
            <div className="border-t border-[#333c52] pt-3">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs text-[#c9a15a] uppercase tracking-wide font-semibold flex items-center gap-1.5">
                  <Crown size={13} />
                  Legendary actions
                  <InfoTooltip text="Typical uses is a suggested default that pre-fills when you add this monster to an encounter (per-encounter, not per-round) - the real expected uses for a given fight, e.g. 'this boss will probably use its tail attack about 3 times this whole encounter,' is set per-encounter in the Adventuring Day tab, since it can reasonably vary fight to fight. to hit/dmg dice/die sides/flat dmg work like a normal attack." />
                </span>
                <button onClick={() => onChange({ legendary_actions: [...m.legendary_actions, newLegendaryAction()] })} className="text-[10.5px] text-[#c9a15a] flex items-center gap-0.5">
                  <Plus size={11} />
                  add
                </button>
              </div>
              <Field label="Legendary resistances (uses/encounter)" hint="Converts this many of the party's failed-save spell casts against this monster into automatic successes this encounter, per the real 5e rule - reduces the expected damage those casts deal. Only affects save-based spells (a spell attack roll isn't a saving throw, so this has no effect on those).">
                <NumberInput value={m.legendary_resistances} onChange={(e) => onChange({ legendary_resistances: +e.target.value || 0 })} />
              </Field>
              <div className="space-y-1.5 mt-2">
                {m.legendary_actions.map((a, i) => (
                  <div key={a.id} className="grid grid-cols-12 gap-1 items-center bg-[#141821] rounded-sm px-2 py-1.5 border border-[#c9a15a]/25">
                    <input className="col-span-3 bg-transparent text-xs focus:outline-none" value={a.name} onChange={(e) => updateLegendary(i, { name: e.target.value })} />
                    <MiniField label="typical uses">
                      <NumberInput value={a.default_uses_per_encounter} onChange={(e) => updateLegendary(i, { default_uses_per_encounter: +e.target.value || 0 })} className="!py-0.5 !text-xs" />
                    </MiniField>
                    <MiniField label="to hit">
                      <NumberInput value={a.to_hit} onChange={(e) => updateLegendary(i, { to_hit: +e.target.value || 0 })} className="!py-0.5 !text-xs" />
                    </MiniField>
                    <DamageDiceFields item={a} onUpdate={(patch) => updateLegendary(i, patch)} />
                    <Select value={a.damage_type} onChange={(e) => updateLegendary(i, { damage_type: e.target.value })} className="col-span-2 !py-0.5 !text-[10px]">
                      {referenceData.damage_types.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </Select>
                    <button onClick={() => removeLegendary(i)} className="col-span-1 text-[#5c6478] hover:text-[#b3452c] flex justify-center">
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
                {m.legendary_actions.length === 0 && <p className="text-[11px] text-[#5c6478] italic">No legendary actions yet. 3 per round is the classic baseline for a solo boss.</p>}
              </div>
            </div>
          )}
        </div>
      )}
    </Panel>
  );
}
