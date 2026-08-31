export const uid = () => Math.random().toString(36).slice(2, 10);

export const ABILITIES = ["str", "dex", "con", "int", "wis", "cha"];

export function newCharacter() {
  return {
    id: uid(), name: "New Adventurer", cls: "Fighter", subclass: "Champion", level: 5,
    ac: 16, max_hp: 45,
    ability_scores: { str: 16, dex: 12, con: 14, int: 10, wis: 10, cha: 10 },
    saving_throw_proficiencies: null, // null = auto-suggest from class; set an array to override
    attack_ability_mod: 4, magic_weapon_bonus: 0, flat_damage_bonus: 4,
    num_attacks: 1, weapon_die_count: 2, weapon_die_sides: 6,
    weapon_damage_type: "slashing", attack_is_magical: false,
    rider_dice_count: 0, rider_die_sides: 6, rider_damage_type: "slashing",
    is_caster: false, use_cantrip: false, cantrip_die_override: null,
    cantrip_id: null, spell_attack_bonus: null, spell_save_dc: null,
    feats: { gwm: false, ss: false, pam: false, cbe: false, savage: false, dueling_style: false, archery_style: false },
    resources: [], resistances: [], vulnerabilities: [], immunities: [],
  };
}

export function newMonster() {
  return {
    id: uid(), name: "New Monster", ac: 15, max_hp: 90, xp: 1800, is_legendary: false,
    save_bonuses: { str: 0, dex: 0, con: 0, int: 0, wis: 0, cha: 0 },
    attacks: [{ id: uid(), name: "Bite", count: 1, to_hit: 6, die_count: 2, die_sides: 8, flat_bonus: 4, damage_type: "piercing", magical: false }],
    save_attacks: [], legendary_actions: [], legendary_resistances: 0, spells: [],
    resistances: [], vulnerabilities: [], immunities: [],
  };
}

export function newAttack() {
  return { id: uid(), name: "Attack", count: 1, to_hit: 5, die_count: 1, die_sides: 8, flat_bonus: 3, damage_type: "slashing", magical: false };
}
export function newSaveAttack() {
  return { id: uid(), name: "Breath Weapon", dc: 14, die_count: 8, die_sides: 6, save_ability: "dex", flat_bonus: 0, damage_type: "fire", magical: true, half_on_save: true, default_uses_per_encounter: 1 };
}
export function newLegendaryAction() {
  return { id: uid(), name: "Legendary Attack", default_uses_per_encounter: 3, to_hit: 8, die_count: 1, die_sides: 10, flat_bonus: 5, damage_type: "slashing", magical: true };
}
export function newMonsterSpell() {
  return { id: uid(), spell_id: "fire_bolt", default_uses_per_encounter: 1, spell_attack_bonus: 6, spell_save_dc: 13 };
}
export function newCustomSpell() {
  return {
    id: uid(), name: "New Spell", level: 1, damage_type: "force",
    mode: "attack", save_ability: "dex", half_on_save: true,
    base_avg: 10, per_level_avg: 3.5,
    bonus_action: false, shape: null, size: null, aoe_targets: null,
  };
}

export function newEncounter(bestiary) {
  return {
    type: "encounter", id: uid(), name: "Encounter",
    monsters: bestiary[0] ? [{ bestiary_id: bestiary[0].id, count: 1 }] : [],
    spends: {}, hp_overrides: {}, monster_uses: {},
  };
}
export function newRest(kind) {
  return { type: "rest", id: uid(), rest_type: kind, heals: {} };
}
