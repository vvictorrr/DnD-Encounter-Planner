import React from "react";
import { Panel } from "./ui.jsx";

export function GuideTab() {
  return (
    <div className="max-w-3xl space-y-5 text-sm text-[#c7cbd6] leading-relaxed">
      <Panel className="p-5">
        <h3 className="font-display font-bold text-lg mb-2 text-[#e9e4d8]">What this tool actually computes</h3>
        <ul className="list-disc pl-5 space-y-2 mt-2">
          <li>
            <b>Monsters are built, not looked up.</b> Every monster in the Bestiary is its own stat block: attacks with real damage
            types, save-based AoEs, resistances/vulnerabilities/immunities, innate spellcasting, and legendary actions for bosses.
            CR only shows up as an optional "seed" button to fill in plausible starting numbers.
          </li>
          <li>
            <b>Subclass changes what a class can do.</b> Only a Battle Master Fighter gets Superiority Dice; only an Eldritch Knight
            Fighter or Arcane Trickster Rogue gets bonus spellcasting. Subclasses calibrated against the community DPR spreadsheet
            (Barbarian, Bard, Artificer) get a flat signature-feature damage bonus; everything else defaults to 0 rather than a guess.
          </li>
          <li>
            <b>Spells are real spells.</b> Pick known/prepared spells from the built-in list or your own Spell Library, and the
            engine computes actual upcast damage (attack roll, saving throw, or auto-hit) against the specific monsters in each
            encounter, including their resistances. Nothing picked falls back to a generic placeholder average.
          </li>
          <li>
            <b>Classic 2014 DMG XP-budget difficulty</b> (per-character thresholds with the monster-count multiplier) runs alongside
            <b> a rounds-to-kill race</b>, which is the part flat XP math misses.
          </li>
          <li>
            <b>A day doesn't have to start at full health.</b> Set starting HP/resources if the party is picking up mid-adventure,
            and after each encounter you can overwrite the predicted outcome with what actually happened at the table. That's what
            carries forward into the next fight, not the raw prediction.
          </li>
        </ul>
      </Panel>
      <Panel className="p-5">
        <h3 className="font-display font-bold text-lg mb-2 text-[#e9e4d8]">Why 2014 rules only</h3>
        <p>
          The community DPR data this project calibrates against ("The Optimists' Guide to D&amp;D 5E Damage by Class") is
          2014-rules math, and the two editions' subclasses and spell lists diverge enough that supporting both faithfully would
          mean either a second full dataset or a misleading "one size fits both" approximation. Better to be exactly right about
          one edition than vaguely right about two.
        </p>
      </Panel>
      <Panel className="p-5">
        <h3 className="font-display font-bold text-lg mb-2 text-[#e9e4d8]">Known simplifications</h3>
        <ul className="list-disc pl-5 space-y-1.5">
          <li>Feats are paused for now and not shown in the Party editor, though the underlying math is still there for when they come back.</li>
          <li>Multi-monster-group encounters blend resistances and damage-type mix across groups by HP/DPR share, rather than simulating optimal focus fire.</li>
          <li>Incoming monster damage is spread across the party by average share, adjusted per-character by their own AC/saves/resistances, rather than simulating focus fire on the squishiest target.</li>
          <li>Legendary Resistance converts a limited number of the party's failed saves against that monster into automatic successes each encounter (the real 5e rule), reducing the expected damage from save-based spells - it only affects saving throws, not spell attack rolls or a character's own at-will/ongoing damage (Rage, weapon attacks, ...).</li>
          <li>AoE spells estimate their target count from their real shape and size (sphere/cube/cone/line/cylinder), capped by however many enemies actually exist in a given encounter - a narrow line genuinely covers less ground than a sphere of a comparable size stat, and neither ever assumes it hits everyone.</li>
        </ul>
      </Panel>
      <Panel className="p-5">
        <h3 className="font-display font-bold text-lg mb-2 text-[#e9e4d8]">Workflow</h3>
        <ol className="list-decimal pl-5 space-y-1.5">
          <li>Build your party in <b>Party</b>: class, subclass, ability scores, damage types, known spells, resistances, and resource pools.</li>
          <li>Optionally build reusable spells in <b>Spell Library</b> if the built-in list doesn't cover something you need.</li>
          <li>Build your monsters in <b>Bestiary</b>: attacks, save-based AoEs, resistances/vulnerabilities/immunities, innate spells, and legendary actions for bosses.</li>
          <li>Lay out the day in <b>Adventuring Day</b>: set starting conditions, add encounters (pulling monster groups from the Bestiary) and rests in order, allocate resource spend per fight, and edit the actual outcome if it played out differently.</li>
          <li>Check <b>Analysis</b> for the whole-day picture: HP trajectory, per-encounter verdicts, and resource burn-down.</li>
        </ol>
      </Panel>
    </div>
  );
}
