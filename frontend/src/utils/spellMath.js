// Lightweight client-side mirrors of backend/app/engine math, used only for
// "reference" numbers shown while editing - the numbers that actually drive
// encounter difficulty always come from POST /api/simulate.

export function abilityMod(score) {
  return Math.floor((score - 10) / 2);
}

export function profBonus(level) {
  return 2 + Math.floor((Math.max(1, level) - 1) / 4);
}

export function hitChance(bonus, target) {
  const needed = Math.max(2, Math.min(20, target - bonus));
  return (21 - needed) / 20;
}

export function dieAvg(count, sides) {
  return (count * (sides + 1)) / 2;
}

/**
 * Expected damage from `count` copies of an attack routine (a die_count/die_sides
 * damage roll plus a flat bonus) against a target AC, crit-weighted - the
 * same hit/crit-split formula used for both a character's weapon attacks and
 * a monster's attack list, so it only needs to live in one place.
 */
export function expectedAttackDamage(count, toHit, targetAc, dieCount, dieSides, flatBonus) {
  const hp = hitChance(toHit, targetAc);
  const critChance = 1 / 20;
  const normal = Math.max(0, hp - critChance);
  const d = dieAvg(dieCount, dieSides);
  const perHit = d + flatBonus;
  const perCrit = 2 * d + flatBonus;
  return count * (critChance * perCrit + normal * perHit);
}

// 2014 PHB hit die per class.
const HIT_DIE = {
  Barbarian: 12, Fighter: 10, Paladin: 10, Ranger: 10,
  Bard: 8, Cleric: 8, Druid: 8, Monk: 8, Rogue: 8, Warlock: 8, Artificer: 8,
  Sorcerer: 6, Wizard: 6,
};

/** The PHB's fixed "average roll" for one hit die: half the die's sides, rounded up, plus one. */
function averageHitDie(sides) {
  return Math.floor(sides / 2) + 1;
}

/**
 * Standard expected max HP: max hit die + CON modifier at level 1, then the
 * average hit die roll (rounded up, per the PHB's fixed-value option) + CON
 * modifier for every level after that.
 */
export function expectedMaxHp(cls, level, conMod) {
  const die = HIT_DIE[cls] || 8;
  const avg = averageHitDie(die);
  const lvl = Math.max(1, level);
  return die + conMod + (lvl - 1) * (avg + conMod);
}

const SAVE_PROFICIENCIES = {
  Artificer: ["con", "int"], Barbarian: ["str", "con"], Bard: ["dex", "cha"],
  Cleric: ["wis", "cha"], Druid: ["int", "wis"], Fighter: ["str", "con"],
  Monk: ["str", "dex"], Paladin: ["wis", "cha"], Ranger: ["str", "dex"],
  Rogue: ["dex", "int"], Sorcerer: ["con", "cha"], Warlock: ["wis", "cha"],
  Wizard: ["int", "wis"],
};

/** A character's saving-throw bonus for one ability - mirrors character.save_bonus_for. */
export function saveBonusFor(c, ability) {
  const score = c.ability_scores?.[ability] ?? 10;
  const mod = abilityMod(score);
  const profs = c.saving_throw_proficiencies ?? SAVE_PROFICIENCIES[c.cls] ?? [];
  const prof = profs.includes(ability) ? profBonus(c.level) : 0;
  return mod + prof;
}

const CASTING_ABILITY = {
  Wizard: "int", Artificer: "int", Fighter: "int", Rogue: "int",
  Sorcerer: "cha", Bard: "cha", Warlock: "cha", Paladin: "cha",
  Cleric: "wis", Druid: "wis", Ranger: "wis",
};

export function spellAttackBonusFor(c) {
  if (c.spell_attack_bonus != null) return c.spell_attack_bonus;
  const ability = CASTING_ABILITY[c.cls] || "int";
  return abilityMod(c.ability_scores?.[ability] ?? 10) + profBonus(c.level);
}

export function spellSaveDcFor(c) {
  if (c.spell_save_dc != null) return c.spell_save_dc;
  const ability = CASTING_ABILITY[c.cls] || "int";
  return 8 + abilityMod(c.ability_scores?.[ability] ?? 10) + profBonus(c.level);
}

/** Mirrors spells.py::dice_avg_for_slot */
function diceAvgForSlot(spell, slotLevel) {
  const extra = Math.max(0, slotLevel - spell.level);
  return spell.base_avg + extra * (spell.per_level_avg || 0);
}

/**
 * Reference expected damage for a leveled spell cast at `slotLevel`, against
 * a neutral AC 15 / DC 13 / target save bonus +2 baseline - purely for
 * showing a meaningful number next to a resource in the Party editor.
 * Mirrors spells.py::expected_leveled_spell_damage.
 */
export function referenceSpellDamage(spell, slotLevel, { attackBonus = 5, targetAc = 15, saveDc = 13, targetSaveBonus = 2 } = {}) {
  const dmg = diceAvgForSlot(spell, slotLevel);
  if (spell.mode === "auto") return dmg;
  if (spell.mode === "attack") {
    const hp = hitChance(attackBonus, targetAc);
    const crit = 1 / 20;
    const normal = Math.max(0, hp - crit);
    return normal * dmg + crit * dmg * 2;
  }
  if (spell.mode === "save") {
    const success = hitChance(targetSaveBonus, saveDc);
    const half = spell.half_on_save ? dmg * 0.5 : 0;
    return (1 - success) * dmg + success * half;
  }
  return dmg;
}

// Calibrated so a 20-ft-radius sphere (Fireball) works out to about 3
// targets in a reasonably spread-out fight - mirrors spells.py::estimate_aoe_targets.
const AREA_PER_TARGET_SQFT = 400;

/** A rough, shape-aware estimate of how many targets an area of effect
 * catches - a narrow line/cone genuinely covers less ground than a sphere
 * or cube of a comparable size stat, since 5e cones are a right-triangle
 * shape (width at any point = distance from the origin). Floored at 2, not
 * 1 - no reasonable DM burns an AoE on a single target; the final
 * targets_hit-style cap elsewhere can still clamp down to 1 if only one
 * enemy actually exists in a given fight. */
export function estimateAoeTargets(shape, size, width = 5) {
  let area;
  if (shape === "sphere" || shape === "cylinder") area = Math.PI * size ** 2;
  else if (shape === "cube") area = size ** 2;
  else if (shape === "cone") area = 0.5 * size ** 2;
  else if (shape === "line") area = size * width;
  else return 1;
  return Math.max(2, Math.round(area / AREA_PER_TARGET_SQFT));
}
