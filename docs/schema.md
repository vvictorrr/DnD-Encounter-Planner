# Data schema

The frontend and backend agree on a handful of plain JSON shapes. There's no
ORM-generated client and no shared TypeScript types - this document is the
contract. Everything is snake_case to match the Python side.

## Character

```jsonc
{
  "id": "uuid-string",
  "name": "Aria Stormblade",
  "cls": "Fighter",                 // one of engine.classes_data.CLASS_LIST
  "subclass": "Battle Master",      // one of engine.classes_data.SUBCLASSES[cls]
  "level": 5,
  "ac": 16,
  "max_hp": 45,

  "attack_ability_mod": 4,
  "magic_weapon_bonus": 1,
  "flat_damage_bonus": 4,
  "num_attacks": 2,
  "weapon_die_count": 2,
  "weapon_die_sides": 6,
  "weapon_damage_type": "slashing",  // one of engine.damage_types.DAMAGE_TYPES
  "attack_is_magical": true,

  "rider_dice_count": 0,             // Sneak Attack / Hunter's Mark / Hex - once per turn
  "rider_die_sides": 6,
  "rider_damage_type": "slashing",

  "is_caster": false,
  "use_cantrip": false,              // true => at-will damage comes from a cantrip, not a weapon
  "cantrip_die_override": null,      // manual override if no cantrip is known
  "known_spells": ["fireball"],      // spell ids from engine.spells.SPELLS the character has prepared

  "spell_attack_bonus": null,        // optional override; defaults to ability mod + proficiency
  "spell_save_dc": null,             // optional override; defaults to 8 + ability mod + proficiency
  "save_bonus": 13,                  // this character's own save bonus vs. monster save-based attacks

  "feats": { "gwm": false, "ss": false, "pam": false, "cbe": false,
             "savage": false, "dueling_style": false, "archery_style": false },

  "resources": [ /* Resource, see below */ ],
  "resistances": [ /* ResistanceEntry, see below */ ],
  "vulnerabilities": [ /* ResistanceEntry */ ],
  "immunities": [ /* ResistanceEntry */ ]
}
```

## Resource

A limited-use pool: spell slots, Rage charges, Ki points, Superiority Dice, ...

```jsonc
{
  "name": "Wizard Lv3 Slots",
  "max": 4,
  "regen": "long",              // "short" | "long"
  "timing": "burst",             // "burst" (default) | "ongoing" - see below
  "displaces_at_will": true,      // only meaningful on a "burst" - see below
  "slot_level": 3,               // only present on spell-slot resources
  "spell_id": "fireball",        // optional - see engine.spells.SPELLS; overrides avg_value/damage_type
  "avg_value": 24.5,             // fallback average damage per use, if no spell_id is set
  "damage_type": "force",        // fallback type; the sentinel "weapon" inherits the character's own weapon
  "magical": true
}
```

`timing` determines how a spent resource turns into damage:

* **`"burst"`** (default) - a one-time lump of damage from a single use (a
  spell slot, Ki, Superiority Dice, Divine Smite, Action Surge). `avg_value`
  (or the linked spell's real damage) is averaged across the encounter's
  assumed rounds. Multiple burst resources can be spent in the same
  encounter independently - e.g. Sorcery Points on a Metamagic option
  alongside a spell slot in the same turn - since the engine works at
  per-encounter resource budgets, not per-turn action economy.

  A burst can also be flagged `displaces_at_will`: casting a leveled spell
  uses the same action a cantrip/weapon swing would have, so it replaces
  one round's worth of at-will damage rather than stacking on top of a full
  turn of it. Spell slots default `true`; Divine Smite, Superiority Dice,
  and Action Surge default `false`, since they trigger on an attack the
  character is already making (or grant an additional one) rather than
  costing the character's normal action.
* **`"ongoing"`** - Rage: activated once, then applies to every attack for
  the rest of the fight. Folded into the character's flat damage bonus
  instead of being divided across rounds, so it scales with however many
  attacks they actually make.

## ResistanceEntry

```jsonc
{ "type": "fire", "magical_only": false }
```

`magical_only: true` means the resistance/vulnerability/immunity only applies
to *nonmagical* instances of that damage type (the classic "resistant to
nonmagical bludgeoning/piercing/slashing").

## Monster

```jsonc
{
  "id": "uuid-string",
  "name": "Young Red Dragon",
  "ac": 18,
  "max_hp": 178,
  "xp": 3900,                 // only used for the classic XP-budget difficulty label
  "save_bonuses": { "str": 7, "dex": 2, "con": 5, "int": 1, "wis": 3, "cha": 4 },
  "is_legendary": false,

  "attacks": [
    { "name": "Bite", "count": 1, "to_hit": 10, "die_count": 2, "die_sides": 10,
      "flat_bonus": 6, "damage_type": "piercing", "magical": false }
  ],
  "save_attacks": [
    { "name": "Fire Breath", "dc": 17, "die_count": 16, "die_sides": 6, "save_ability": "dex",
      "flat_bonus": 0, "damage_type": "fire", "magical": true, "half_on_save": true,
      "default_uses_per_encounter": 1, "displaces_action": true }
  ],
  "spells": [
    { "spell_id": "fireball", "spell_save_dc": 17, "default_uses_per_encounter": 1, "displaces_action": true }
  ],
  "legendary_actions": [
    { "name": "Tail Attack", "default_uses_per_encounter": 3, "to_hit": 10,
      "die_count": 2, "die_sides": 8, "flat_bonus": 6, "damage_type": "bludgeoning", "magical": true }
  ],
  "legendary_resistances": 3,   // real effect on the party's save-based spell damage - see below

  "resistances": [], "vulnerabilities": [], "immunities": []
}
```

`attacks` are the monster's baseline turn - unconditional, every round, the
same way a character's cantrip is. `save_attacks`, `spells`, and
`legendary_actions` aren't guaranteed every round, so `default_uses_per_encounter`
is a plain **suggested total for a typical fight** (not a per-round rate) -
the real number for a specific encounter is set in the Adventuring Day tab's
`monster_uses` (see below), not baked into the stat block here. The total is
also capped at however many rounds the fight actually takes - a monster
can't use a special ability more times than it has turns, so setting the
number very high correctly clamps to "fires every round" rather than
inflating the damage past what's physically possible.

`legendary_resistances` (only relevant when `is_legendary` is true) converts
this many of the party's failed-save spell casts against this monster into
automatic successes this encounter - the real 5e rule, not just a reference
number. Computed once per encounter as a coverage fraction: total save-based
casts across the whole party this encounter, capped at however many the
monster can actually resist, blended into each affected cast's expected
damage. Only save-based spells are affected (a spell attack roll isn't a
saving throw, so Legendary Resistance has no bearing on it), and it has no
effect on a character's own at-will or ongoing damage (Rage, weapon
attacks, ...) - a boss can't legendary-resist its way out of just getting
hit by a sword.

`displaces_action` (default `true` on `save_attacks` and `spells`) means
using that ability replaces one round's worth of the monster's own
`attacks` rather than stacking on top of them - a dragon doesn't bite AND
breathe fire the same turn. `legendary_actions` never displace; they fire
on *other* creatures' turns, genuinely in addition to the monster's own
turn, which is the whole point of them being "legendary."

## Spell (built-in or custom, from the Spell Library)

```jsonc
{
  "id": "fireball",
  "name": "Fireball",
  "level": 3,
  "damage_type": "fire",
  "mode": "save",                // "attack" | "save" | "auto"
  "save_ability": "dex",         // only present when mode == "save"
  "half_on_save": true,
  "base_avg": 28.0,              // average damage at this spell's minimum level
  "per_level_avg": 3.5,          // extra average damage per slot level spent upcasting
  "bonus_action": false,         // true = doesn't cost the caster's normal action (Spiritual Weapon, Hail of Thorns)
  "shape": "sphere",             // "sphere" | "cube" | "cone" | "line" | "cylinder" - omit for single-target
  "size": 20,                    // the shape's defining dimension in feet (radius/side/length)
  "width": 5                     // line-only, defaults to 5 ft
}
```

`bonus_action` sets the default for a spell-slot resource's "replaces
action" checkbox the moment it's picked - a bonus-action spell doesn't cost
the turn a cantrip/attack would have used, so it shouldn't displace one.

`shape`/`size` estimate how many targets a genuine area-of-effect spell
hits from its *real footprint*, rather than a single hand-picked number per
spell - a narrow line or cone genuinely covers less ground than a sphere or
cube of a comparable size stat (5e cones are a right-triangle shape: width
at any point equals the distance from the origin, so a cone's area is half
of `size²`). See `estimate_aoe_targets` in `app.engine.spells` for the exact
formula. The result is always capped at however many targets actually exist
in a given encounter (`targets_hit`) - never assumed to hit everyone.

A spell can instead carry an explicit `aoe_targets` override for targeting
that isn't really an area shape at all - Chain Lightning's "+3 additional
targets" rule, for example. An explicit `aoe_targets` always takes
precedence over `shape`/`size` if both are somehow present.

## Day plan (`items`)

A list of encounters and rests, in the order they'll be run:

```jsonc
[
  { "type": "encounter", "id": "e1", "name": "Ambush at the bridge",
    "monsters": [ { "bestiary_id": "goblin-uuid", "count": 4 } ],
    "spends": { "character-uuid": { "Wizard Lv3 Slots": 1 } },
    "monster_uses": { "goblin-uuid": { "Fire Breath": 1, "Fireball (innate)": 1 } } },
  { "type": "rest", "id": "r1", "rest_type": "short", "heals": { "character-uuid": 15 } },
  { "type": "encounter", "id": "e2", "name": "The dragon's lair",
    "monsters": [ { "bestiary_id": "dragon-uuid", "count": 1 } ], "spends": {} }
]
```

There's no `rounds_assumed` input anymore - how long a fight actually takes
is computed, not guessed: the engine solves for the round count at which the
party's damage output would kill the monsters *or* the monster's damage
would drop the most vulnerable character, whichever happens first, and uses
that self-consistent value everywhere a "how many rounds does this burst
average over" question comes up. The response's `rounds_assumed` field (see
below) reports what that computed value turned out to be.

`monster_uses` is the per-encounter override for how many times each of a
monster's special abilities (breath weapons, innate spells, legendary
actions - anything other than its baseline `attacks`) actually fires in
*this specific fight* - a plain total for the whole encounter, not a rate.
Keyed by `bestiary_id`, then by the ability's display name (a save-attack's
own `name`, an innate spell as `"<Spell Name> (innate)"`, or a legendary
action as `"<name> (legendary)"`). Falls back to that ability's own
`default_uses_per_encounter` (a suggested guess set in the Bestiary) when
there's no override here.

A rest's `heals` (only meaningful on a short rest - a long rest already fully
restores HP) is Hit Dice/healing actually spent, added to whatever HP a
character had going in, capped at their max. Sparse and optional; a
character with no entry there gets no healing on that rest.

## `POST /api/simulate` response

```jsonc
{
  "snapshots": [
    { /* per-encounter result */ },
    null,               // a rest has no snapshot
    { /* per-encounter result */ }
  ]
}
```

Each non-null snapshot:

```jsonc
{
  "total_monster_hp": 178, "monster_dpr_total": 34.2, "total_xp": 3900,
  "avg_monster_ac": 18, "avg_party_ac": 16.5,
  "party_dpr_total": 41.7,
  "rounds_to_kill_monsters": 4.3, "rounds_to_drop_pc": 3.1,
  "label": { "text": "Deadly", "tone": "danger", "budget": 6400 },
  "resources_before": { "character-uuid": { "Wizard Lv3 Slots": 4 } },
  "warnings": ["A character could realistically go down in 2 rounds or less. Expect deaths without smart play."],
  "hp_before": { "character-uuid": 45 },
  "predicted_hp_after": { "character-uuid": 12 },
  "hp_after": { "character-uuid": 12 },
  "damage_mix_note": "Party damage is already discounted/boosted for these monsters' resistances, vulnerabilities and immunities."
}
```

`hp_before` is what each character actually had entering this fight (after any
prior override was applied). `predicted_hp_after` is the engine's raw
computed prediction, untouched. `hp_after` is what actually carries forward -
equal to the prediction unless this encounter's `hp_overrides` supplied a
different value.
