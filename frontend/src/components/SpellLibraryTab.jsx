import { Plus, Trash2 } from "lucide-react";
import React from "react";
import { newCustomSpell } from "../utils/factories.js";
import { estimateAoeTargets } from "../utils/spellMath.js";
import { Checkbox, Field, NumberInput, Panel, Select, TextInput } from "./ui.jsx";

export function SpellLibraryTab({ customSpells, setCustomSpells, referenceData }) {
  const updateSpell = (id, patch) => setCustomSpells((list) => list.map((s) => (s.id === id ? { ...s, ...patch } : s)));
  const removeSpell = (id) => setCustomSpells((list) => list.filter((s) => s.id !== id));
  const addSpell = () => setCustomSpells((list) => [...list, newCustomSpell()]);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-sm text-[#8b93a7] max-w-2xl">
          Build a spell once here and it becomes pickable anywhere a character's known-spells list shows up, exactly
          like the built-in list. No damage type, save, or upcast math needs to be hardcoded ahead of time; you define
          it directly.
        </p>
        <button onClick={addSpell} className="flex items-center gap-1.5 bg-[#c9a15a] text-[#14171f] font-semibold rounded-sm px-3 py-2 text-sm hover:bg-[#d8b06c]">
          <Plus size={15} /> New spell
        </button>
      </div>

      {customSpells.length === 0 && (
        <Panel className="p-8 text-center text-[#8b93a7] text-sm">
          No custom spells yet. The built-in list (Fire Bolt, Fireball, and about 30 others) already works everywhere;
          add one here only when you need something it doesn't cover.
        </Panel>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        {customSpells.map((s) => (
          <Panel key={s.id} className="p-4">
            <div className="flex items-start justify-between gap-3 mb-3">
              <TextInput value={s.name} onChange={(e) => updateSpell(s.id, { name: e.target.value })} />
              <button onClick={() => removeSpell(s.id)} className="p-1.5 text-[#8b93a7] hover:text-[#b3452c] shrink-0">
                <Trash2 size={16} />
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <Field label="Level" hint="0 = cantrip (scales by character level tier instead of upcasting)">
                <NumberInput value={s.level} onChange={(e) => updateSpell(s.id, { level: Math.max(0, +e.target.value || 0) })} />
              </Field>
              <Field label="Damage type">
                <Select value={s.damage_type} onChange={(e) => updateSpell(s.id, { damage_type: e.target.value })}>
                  {referenceData.damage_types.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Resolves via" hint="attack = spell attack roll vs AC. save = target rolls a save. auto = always hits, no roll (Magic Missile-style).">
                <Select value={s.mode} onChange={(e) => updateSpell(s.id, { mode: e.target.value })}>
                  <option value="attack">attack roll</option>
                  <option value="save">saving throw</option>
                  <option value="auto">automatic hit</option>
                </Select>
              </Field>
              {s.mode === "save" && (
                <Field label="Save ability">
                  <Select value={s.save_ability} onChange={(e) => updateSpell(s.id, { save_ability: e.target.value })}>
                    {referenceData.abilities.map((a) => (
                      <option key={a} value={a}>
                        {a.toUpperCase()}
                      </option>
                    ))}
                  </Select>
                </Field>
              )}
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
              <Field
                label={s.level === 0 ? "Damage per tier" : "Base avg damage"}
                hint={s.level === 0 ? "Average damage per instance at the lowest tier (levels 1-4)." : "Average damage at this spell's minimum level."}
              >
                <NumberInput value={s.base_avg} onChange={(e) => updateSpell(s.id, { base_avg: +e.target.value || 0 })} />
              </Field>
              {s.level > 0 && (
                <Field label="Extra avg / level upcast" hint="Additional average damage per slot level spent above this spell's minimum level. 0 if it doesn't scale.">
                  <NumberInput value={s.per_level_avg} onChange={(e) => updateSpell(s.id, { per_level_avg: +e.target.value || 0 })} />
                </Field>
              )}
              {s.mode === "save" && (
                <div className="flex items-end pb-1.5">
                  <Checkbox checked={s.half_on_save} onChange={(e) => updateSpell(s.id, { half_on_save: e.target.checked })} label="Half damage on a successful save" />
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2 mt-2">
              <Field
                label="Bonus action?"
                hint="Casting this doesn't cost the character's normal action, so it doesn't replace a turn's cantrip/attack the way a full-action spell would. Sets the default for a slot's 'replaces action' checkbox when this spell is picked."
              >
                <div className="pt-1.5">
                  <Checkbox checked={!!s.bonus_action} onChange={(e) => updateSpell(s.id, { bonus_action: e.target.checked })} label="Bonus action cast" />
                </div>
              </Field>
              <Field
                label="Area shape"
                hint="Not just single-target. A narrow line/cone genuinely catches fewer enemies than a sphere/cube of a comparable size - so the number of targets it hits is estimated from its real footprint, not typed in directly."
              >
                <Select
                  value={s.shape || ""}
                  onChange={(e) => {
                    const shape = e.target.value || null;
                    updateSpell(s.id, shape ? { shape, size: s.size ?? 20, aoe_targets: null } : { shape: null, size: null });
                  }}
                >
                  <option value="">single target</option>
                  <option value="sphere">sphere (radius)</option>
                  <option value="cube">cube (side)</option>
                  <option value="cone">cone (length)</option>
                  <option value="line">line (length, 5 ft wide)</option>
                </Select>
              </Field>
            </div>
            {s.shape && (
              <div className="grid grid-cols-2 gap-2 mt-2 items-end">
                <Field label={`${s.shape[0].toUpperCase()}${s.shape.slice(1)} size (ft)`}>
                  <NumberInput value={s.size ?? 20} min={5} onChange={(e) => updateSpell(s.id, { size: Math.max(5, +e.target.value || 5) })} />
                </Field>
                <p className="text-[10.5px] text-[#8b93a7] pb-1.5">
                  ~{estimateAoeTargets(s.shape, s.size ?? 20)} targets in a typical fight (capped at however many enemies actually exist in a given encounter)
                </p>
              </div>
            )}
          </Panel>
        ))}
      </div>
    </div>
  );
}
