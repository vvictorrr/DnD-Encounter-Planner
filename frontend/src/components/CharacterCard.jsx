import { ChevronDown, ChevronUp, Plus, Trash2 } from "lucide-react";
import React, { useMemo, useState } from "react";
import { api } from "../api/client.js";
import { ABILITIES } from "../utils/factories.js";
import { abilityMod, expectedAttackDamage, expectedMaxHp, dieAvg, estimateAoeTargets, hitChance, profBonus, saveBonusFor } from "../utils/spellMath.js";
import { Checkbox, DamageTypeListEditor, Field, InfoTooltip, NumberInput, Panel, Select, StatCardRow, TextInput } from "./ui.jsx";

// Local mirror of the backend's DPR math, used only for the live "reference
// DPR" readout in this card - the numbers that actually drive encounter
// difficulty always come from POST /api/simulate.
function referenceDpr(c) {
  const toHit = c.attack_ability_mod + profBonus(c.level) + (c.magic_weapon_bonus || 0);
  const hp = hitChance(toHit, 15);
  const main = expectedAttackDamage(c.num_attacks || 0, toHit, 15, c.weapon_die_count, c.weapon_die_sides, c.flat_damage_bonus);
  const rider = hp * dieAvg(c.rider_dice_count || 0, c.rider_die_sides || 6);
  return { dpr: main + rider, hitPct: hp };
}

const ABILITY_LABELS = { str: "STR", dex: "DEX", con: "CON", int: "INT", wis: "WIS", cha: "CHA" };

export function CharacterCard({ c, referenceData, customSpells, onChange, onRemove }) {
  const [expanded, setExpanded] = useState(true);
  const ref = useMemo(() => referenceDpr(c), [c]);
  const subclassOptions = referenceData.subclasses[c.cls] || [];
  const allSpells = useMemo(() => {
    const merged = { ...referenceData.spells };
    for (const s of customSpells) merged[s.id] = s;
    return merged;
  }, [referenceData.spells, customSpells]);
  // Custom spells (from the Spell Library) have no class restriction by design.
  const classSpells = Object.entries(allSpells).filter(([, s]) => !s.classes || s.classes.includes(c.cls));
  const cantripOptions = classSpells.filter(([, s]) => s.level === 0);
  const calibration = referenceData.optimizer_calibration[c.cls];
  const effectiveSaveProfs = c.saving_throw_proficiencies ?? referenceData.save_proficiencies[c.cls] ?? [];

  const resyncResources = async (cls = c.cls, level = c.level, subclass = c.subclass) => {
    const { resources, rider_suggestion } = await api.getResourceTemplate(cls, level, subclass);
    const patch = { resources };
    // Always-on rider effects (Sneak Attack, ...) aren't a spendable resource -
    // they auto-fill the character's own rider-dice fields instead.
    if (rider_suggestion) {
      patch.rider_dice_count = rider_suggestion.dice_count;
      patch.rider_die_sides = rider_suggestion.die_sides;
    }
    onChange(patch);
  };

  const onFeat = (key, val) => onChange({ feats: { ...c.feats, [key]: val } });
  const toggleSaveProficiency = (ability) => {
    const next = effectiveSaveProfs.includes(ability) ? effectiveSaveProfs.filter((a) => a !== ability) : [...effectiveSaveProfs, ability];
    onChange({ saving_throw_proficiencies: next });
  };

  const updateResource = (idx, patch) => onChange({ resources: c.resources.map((r, i) => (i === idx ? { ...r, ...patch } : r)) });
  const addResource = () => onChange({ resources: [...c.resources, { name: "Custom Resource", max: 1, avg_value: 10, regen: "long", timing: "burst", displaces_at_will: false, damage_type: "force", magical: true }] });
  const addSpellSlot = () =>
    onChange({
      resources: [
        ...c.resources,
        { name: "Custom Spell Slot", max: 1, slot_level: 1, regen: "long", spell_id: null, avg_value: 0, displaces_at_will: true, damage_type: "force", magical: true },
      ],
    });
  const removeResource = (idx) => onChange({ resources: c.resources.filter((_, i) => i !== idx) });

  return (
    <Panel className="p-4">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 grid grid-cols-2 gap-2">
          <TextInput value={c.name} onChange={(e) => onChange({ name: e.target.value })} />
          <div className="flex gap-2">
            <Select
              value={c.cls}
              onChange={(e) => {
                const cls = e.target.value;
                const subclass = (referenceData.subclasses[cls] || [])[0] || "";
                onChange({ cls, subclass, is_caster: ["Wizard", "Sorcerer", "Warlock", "Bard", "Druid", "Cleric", "Artificer"].includes(cls), cantrip_id: null });
                resyncResources(cls, c.level, subclass);
              }}
            >
              {referenceData.class_list.map((cl) => (
                <option key={cl}>{cl}</option>
              ))}
            </Select>
            <NumberInput
              value={c.level}
              min={1}
              max={20}
              onChange={(e) => {
                const level = Math.max(1, Math.min(20, +e.target.value || 1));
                onChange({ level });
                resyncResources(c.cls, level, c.subclass);
              }}
              className="w-20"
            />
          </div>
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

      <Select
        value={c.subclass}
        onChange={(e) => {
          onChange({ subclass: e.target.value });
          resyncResources(c.cls, c.level, e.target.value);
        }}
      >
        {subclassOptions.map((s) => (
          <option key={s}>{s}</option>
        ))}
      </Select>

      <div className="mt-3">
        <StatCardRow
          stats={[
            { label: "Ref. DPR @ AC 15", value: ref.dpr.toFixed(1), accent: true, hint: "At-will attacks only - computed before any resources (spell slots, Rage, Action Surge, etc.) are spent this encounter." },
            { label: "Hit chance", value: `${Math.round(ref.hitPct * 100)}%` },
          ]}
        />
      </div>
      {calibration && (
        <p className="text-[10px] text-[#5c6478] mt-1.5 italic">
          Community-optimizer reference (Optimists' Guide to 5E Damage): a strong {c.cls} averages ~{calibration} dmg/round across all levels.
        </p>
      )}

      {expanded && (
        <div className="mt-4 space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <Field label="AC (defense)">
              <NumberInput value={c.ac} onChange={(e) => onChange({ ac: +e.target.value || 0 })} />
            </Field>
            <Field
              label="Max HP"
              hint="The 'compute' button estimates this using the standard formula: max hit die + CON mod at level 1, then average hit die (rounded up) + CON mod per level after."
            >
              <div className="flex gap-1">
                <NumberInput value={c.max_hp} onChange={(e) => onChange({ max_hp: +e.target.value || 1 })} />
                <button
                  onClick={() => onChange({ max_hp: expectedMaxHp(c.cls, c.level, abilityMod(c.ability_scores?.con ?? 10)) })}
                  className="shrink-0 text-[10.5px] text-[#8b93a7] hover:text-[#c9a15a] border border-[#333c52] rounded-sm px-2"
                  title="Compute expected max HP from class hit die, level, and CON"
                >
                  compute
                </button>
              </div>
            </Field>
            <Field label="Attack ability mod" hint="STR/DEX mod used for weapon attacks specifically">
              <NumberInput value={c.attack_ability_mod} onChange={(e) => onChange({ attack_ability_mod: +e.target.value || 0 })} />
            </Field>
          </div>

          <div>
            <span className="text-xs text-[#8b93a7] uppercase tracking-wide font-medium mb-1.5 flex items-center gap-1">
              Ability scores &amp; saving throws
              <InfoTooltip text="Checkbox = proficient in that saving throw (adds proficiency bonus). This is what a monster's breath weapon or a save-based spell actually checks against, not one flat number for every kind of save." />
            </span>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-2 mt-1.5">
              {ABILITIES.map((a) => {
                const proficient = effectiveSaveProfs.includes(a);
                const bonus = saveBonusFor(c, a);
                return (
                  <div key={a} className="bg-[#141821] rounded-sm px-2 py-1.5 border border-[#333c52]">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-[#8b93a7] uppercase font-semibold">{ABILITY_LABELS[a]}</span>
                      <label className="flex items-center gap-1 cursor-pointer" title="Proficient in this saving throw">
                        <input type="checkbox" checked={proficient} onChange={() => toggleSaveProficiency(a)} className="accent-[#c9a15a] w-3 h-3" />
                      </label>
                    </div>
                    <NumberInput
                      value={c.ability_scores?.[a] ?? 10}
                      onChange={(e) => onChange({ ability_scores: { ...c.ability_scores, [a]: +e.target.value || 10 } })}
                      className="!py-0.5 !text-xs mt-1"
                    />
                    <div className="text-[10px] text-[#5c6478] mt-0.5 text-center font-mono2">
                      save {bonus >= 0 ? "+" : ""}{bonus}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {!c.is_caster || !c.use_cantrip ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 items-end">
              <Field label="# Attacks">
                <NumberInput value={c.num_attacks} onChange={(e) => onChange({ num_attacks: +e.target.value || 0 })} />
              </Field>
              <Field label="Weapon dice">
                <div className="flex gap-1">
                  <NumberInput value={c.weapon_die_count} onChange={(e) => onChange({ weapon_die_count: +e.target.value || 0 })} />
                  <span className="self-center text-xs text-[#8b93a7]">d</span>
                  <NumberInput value={c.weapon_die_sides} onChange={(e) => onChange({ weapon_die_sides: +e.target.value || 6 })} />
                </div>
              </Field>
              <Field label="Flat dmg / hit">
                <NumberInput value={c.flat_damage_bonus} onChange={(e) => onChange({ flat_damage_bonus: +e.target.value || 0 })} />
              </Field>
              <Field label="Magic weapon bonus">
                <NumberInput
                  value={c.magic_weapon_bonus}
                  onChange={(e) => {
                    const v = +e.target.value || 0;
                    onChange({ magic_weapon_bonus: v, attack_is_magical: v > 0 ? true : c.attack_is_magical });
                  }}
                />
              </Field>
              <Field label="Weapon damage type">
                <Select value={c.weapon_damage_type} onChange={(e) => onChange({ weapon_damage_type: e.target.value })}>
                  {referenceData.damage_types.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Rider dice" hint="Extra dice added once per turn on a hit (not per attack) - Sneak Attack, Hunter's Mark, Hex. For a Rogue this auto-fills from Sneak Attack when you resync below.">
                <div className="flex gap-1">
                  <NumberInput value={c.rider_dice_count} onChange={(e) => onChange({ rider_dice_count: +e.target.value || 0 })} />
                  <span className="self-center text-xs text-[#8b93a7]">d</span>
                  <NumberInput value={c.rider_die_sides} onChange={(e) => onChange({ rider_die_sides: +e.target.value || 6 })} />
                </div>
              </Field>
              <Field label="Rider damage type">
                <Select value={c.rider_damage_type} onChange={(e) => onChange({ rider_damage_type: e.target.value })}>
                  {referenceData.damage_types.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Select>
              </Field>
              <div className="flex items-end pb-1.5">
                <Checkbox checked={c.attack_is_magical} onChange={(e) => onChange({ attack_is_magical: e.target.checked })} label="Attack counts as magical" />
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              <Field label="Cantrip die avg override" hint="Blank = auto by level (used only if no cantrip is picked below)">
                <NumberInput
                  value={c.cantrip_die_override ?? ""}
                  placeholder="auto"
                  onChange={(e) => onChange({ cantrip_die_override: e.target.value === "" ? null : +e.target.value })}
                />
              </Field>
              <Field label="Flat dmg / hit">
                <NumberInput value={c.flat_damage_bonus} onChange={(e) => onChange({ flat_damage_bonus: +e.target.value || 0 })} />
              </Field>
            </div>
          )}

          <div className="flex flex-wrap gap-3 items-center">
            {c.is_caster && <Checkbox checked={c.use_cantrip} onChange={(e) => onChange({ use_cantrip: e.target.checked })} label="At-will = cantrip (not weapon)" />}
          </div>
          {/* Feats are paused for now (see project notes) - onFeat/referenceData.feats
              are still wired up server-side, just not exposed in this card. */}

          {c.is_caster && c.use_cantrip && (
            <Field label="Cantrip" hint="Which cantrip this character actually casts at-will. Leave blank to fall back to a generic attack-cantrip approximation.">
              <Select value={c.cantrip_id || ""} onChange={(e) => onChange({ cantrip_id: e.target.value || null })}>
                <option value="">(generic fallback)</option>
                {cantripOptions.map(([id, s]) => (
                  <option key={id} value={id}>
                    {s.name} ({s.damage_type}, {s.mode})
                  </option>
                ))}
              </Select>
            </Field>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <span className="text-[10.5px] text-[#8b93a7] uppercase tracking-wide font-medium block mb-1">Your resistances</span>
              <DamageTypeListEditor list={c.resistances} onChange={(l) => onChange({ resistances: l })} damageTypes={referenceData.damage_types} tone="good" />
            </div>
            <div>
              <span className="text-[10.5px] text-[#8b93a7] uppercase tracking-wide font-medium block mb-1">Your vulnerabilities</span>
              <DamageTypeListEditor list={c.vulnerabilities} onChange={(l) => onChange({ vulnerabilities: l })} damageTypes={referenceData.damage_types} tone="danger" />
            </div>
            <div>
              <span className="text-[10.5px] text-[#8b93a7] uppercase tracking-wide font-medium block mb-1">Your immunities</span>
              <DamageTypeListEditor list={c.immunities} onChange={(l) => onChange({ immunities: l })} damageTypes={referenceData.damage_types} tone="neutral" />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs text-[#8b93a7] uppercase tracking-wide font-medium flex items-center gap-1">
                Resource pools
                <InfoTooltip text="Anything limited-use that recharges on a rest: spell slots, Rage, Ki, Superiority Dice, Action Surge. max = uses before a rest refills it (most reset on a long rest; some, like Warlock pact slots, reset on a short rest instead - set per resource below). Every resource has a timing: one-shot burst (a spell slot or Ki point spent once, val = its expected damage, divided across the fight's assumed rounds - stacks freely with other bursts spent the same encounter, e.g. Sorcery Points alongside a spell slot) or ongoing (Rage: applies to every attack for the whole fight once activated, not diluted). A burst can also be marked 'replaces action': casting a leveled spell uses the same action a cantrip/weapon swing would, so it displaces one round of at-will damage instead of stacking on top of it. Checked by default for spell slots and unchecked automatically for spells marked bonus action in the Spell Library (a bonus-action spell doesn't cost your normal action); also unchecked for things like Divine Smite, Superiority Dice, or Action Surge that ride along on / grant an attack rather than replacing one. A spell slot gets a dropdown to pick which spell fills it instead of a flat val." />
              </span>
              <div className="flex gap-2">
                <button onClick={() => resyncResources()} className="text-[10.5px] text-[#8b93a7] hover:text-[#c9a15a] underline">
                  resync from class/level/subclass
                </button>
                <button onClick={addSpellSlot} className="text-[10.5px] text-[#c9a15a] hover:text-[#d8b06c] flex items-center gap-0.5">
                  <Plus size={11} />
                  spell slot
                </button>
                <button onClick={addResource} className="text-[10.5px] text-[#c9a15a] hover:text-[#d8b06c] flex items-center gap-0.5">
                  <Plus size={11} />
                  resource
                </button>
              </div>
            </div>
            <p className="text-[10px] text-[#5c6478] mb-1.5">
              Any character can have a spell slot added, even a class that doesn't normally cast spells. Wizards,
              Eldritch Knights, Arcane Tricksters, and other real casters get theirs added automatically on resync.
            </p>
            <div className="space-y-1.5">
              {c.resources.length === 0 && <p className="text-[11px] text-[#5c6478] italic">No tracked resources (pure at-will attacker).</p>}
              {c.resources.map((r, i) => {
                const isSpellSlot = r.slot_level != null;
                if (isSpellSlot) {
                  const options = classSpells.filter(([, s]) => s.level > 0 && s.level <= r.slot_level);
                  const chosen = r.spell_id ? allSpells[r.spell_id] : null;
                  return (
                    <div key={i} className="bg-[#141821] rounded-sm px-2 py-1.5 border border-[#333c52] space-y-1">
                      <div className="grid grid-cols-12 gap-1.5 items-center">
                        <input className="col-span-3 bg-transparent text-xs focus:outline-none min-w-0" value={r.name} onChange={(e) => updateResource(i, { name: e.target.value })} />
                        <div className="col-span-2 flex items-center gap-1 min-w-0">
                          <span className="text-[9px] text-[#5c6478] shrink-0">max</span>
                          <NumberInput value={r.max} onChange={(e) => updateResource(i, { max: +e.target.value || 0 })} className="!py-0.5 !text-xs" />
                        </div>
                        <div className="col-span-2 flex items-center gap-1 min-w-0">
                          <span className="text-[9px] text-[#5c6478] shrink-0">slot lvl</span>
                          <NumberInput value={r.slot_level} onChange={(e) => updateResource(i, { slot_level: Math.max(1, +e.target.value || 1) })} className="!py-0.5 !text-xs" />
                        </div>
                        <Select value={r.regen} onChange={(e) => updateResource(i, { regen: e.target.value })} className="col-span-3 !py-0.5 !text-[10.5px]">
                          <option value="short">short rest</option>
                          <option value="long">long rest</option>
                        </Select>
                        <button onClick={() => removeResource(i)} className="col-span-2 text-[#5c6478] hover:text-[#b3452c] flex justify-center">
                          <Trash2 size={13} />
                        </button>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Select
                          value={r.spell_id || ""}
                          onChange={(e) => {
                            const newSpellId = e.target.value || null;
                            const newSpell = newSpellId ? allSpells[newSpellId] : null;
                            updateResource(i, { spell_id: newSpellId, displaces_at_will: !(newSpell?.bonus_action) });
                          }}
                          className="!py-0.5 !text-[10.5px] flex-1"
                        >
                          <option value="">(unassigned, flat placeholder)</option>
                          {options.map(([id, s]) => (
                            <option key={id} value={id}>
                              {s.name} (Lv{s.level}, {s.damage_type}, {s.mode}
                              {s.bonus_action ? ", bonus action" : ""})
                            </option>
                          ))}
                        </Select>
                        <label className="flex items-center gap-1 text-[9.5px] text-[#8b93a7] whitespace-nowrap" title="Casting a leveled spell uses the same action a cantrip/weapon swing would - unchecked automatically for spells marked bonus action in the Spell Library, but you can override it here.">
                          <input type="checkbox" checked={r.displaces_at_will !== false} onChange={(e) => updateResource(i, { displaces_at_will: e.target.checked })} className="accent-[#c9a15a]" />
                          replaces action
                        </label>
                      </div>
                      {chosen ? (
                        <p className="text-[10px] text-[#8fbf8f] pl-0.5">
                          {chosen.damage_type}, {chosen.mode}
                          {chosen.mode === "save" ? ` (${chosen.save_ability} save${chosen.half_on_save ? ", half on success" : ", none on success"})` : ""}
                          {chosen.bonus_action ? ", bonus action" : ""}.{" "}
                          {chosen.base_avg} avg @ Lv{chosen.level}
                          {chosen.per_level_avg ? ` (+${chosen.per_level_avg}/level upcast)` : ""}
                          {(() => {
                            const targets = chosen.shape ? estimateAoeTargets(chosen.shape, chosen.size) : chosen.aoe_targets;
                            return targets > 1 ? ` · AoE, up to ${targets} targets` : "";
                          })()}.
                        </p>
                      ) : (
                        <p className="text-[10px] text-[#5c6478] pl-0.5 italic">No spell picked; uses the flat placeholder average of {r.avg_value || 0}.</p>
                      )}
                    </div>
                  );
                }
                return (
                  <div key={i} className="grid grid-cols-[repeat(13,minmax(0,1fr))] gap-1.5 items-center bg-[#141821] rounded-sm px-2 py-1.5 border border-[#333c52]">
                    <input className="col-span-2 bg-transparent text-xs focus:outline-none min-w-0" value={r.name} onChange={(e) => updateResource(i, { name: e.target.value })} />
                    <div className="col-span-2 flex items-center gap-1 min-w-0">
                      <span className="text-[9px] text-[#5c6478] shrink-0">max</span>
                      <NumberInput value={r.max} onChange={(e) => updateResource(i, { max: +e.target.value || 0 })} className="!py-0.5 !text-xs" />
                    </div>
                    <div className="col-span-2 flex items-center gap-1 min-w-0">
                      <span className="text-[9px] text-[#5c6478] shrink-0">val</span>
                      <NumberInput value={r.avg_value} onChange={(e) => updateResource(i, { avg_value: +e.target.value || 0 })} className="!py-0.5 !text-xs" />
                    </div>
                    <Select value={r.regen} onChange={(e) => updateResource(i, { regen: e.target.value })} className="col-span-2 !py-0.5 !text-[10.5px]">
                      <option value="short">short rest</option>
                      <option value="long">long rest</option>
                    </Select>
                    <Select value={r.timing || "burst"} onChange={(e) => updateResource(i, { timing: e.target.value })} className="col-span-2 !py-0.5 !text-[10.5px]">
                      <option value="burst">one-shot burst</option>
                      <option value="ongoing">ongoing (all fight)</option>
                    </Select>
                    <div className="col-span-2 text-[10px] min-w-0">
                      {r.timing === "burst" || !r.timing ? (
                        <label className="flex items-center gap-1 text-[#8b93a7] cursor-pointer" title="Casting a leveled spell uses the same action a cantrip/weapon swing would - check this if using the resource replaces a normal turn instead of stacking on top of it.">
                          <input type="checkbox" checked={!!r.displaces_at_will} onChange={(e) => updateResource(i, { displaces_at_will: e.target.checked })} className="accent-[#c9a15a]" />
                          replaces action
                        </label>
                      ) : (
                        <span className="text-[#5c6478] truncate block" title={r.note}>
                          {r.note || "n/a"}
                        </span>
                      )}
                    </div>
                    <button onClick={() => removeResource(i)} className="col-span-1 text-[#5c6478] hover:text-[#b3452c] flex justify-center">
                      <Trash2 size={13} />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </Panel>
  );
}
