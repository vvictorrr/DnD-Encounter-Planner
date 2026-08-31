import React from "react";
import { Panel } from "./ui.jsx";

export function GuideTab() {
  return (
    <div className="max-w-3xl space-y-5 text-sm text-[#c7cbd6] leading-relaxed">
      <Panel className="p-5">
        <h3 className="font-display font-bold text-lg mb-2 text-[#e9e4d8]">How it works</h3>
        <p>
          This simulator is intended to be used as a tool to assist in giving DMs a frame of reference to balance
          monsters and encounters across an adventuring day. The simulator assumes every encounter is done with full
          intent to kill, so no turns are spent on non-damage based actions. The simulator also does not take into
          account intelligent monster or player play. For example, you may want to reconsider balancing if you desire
          your party to be ambushed by monsters, give your party the opportunity to ambush monsters, or include
          environmental factors in play.
        </p>
      </Panel>

      <Panel className="p-5">
        <h3 className="font-display font-bold text-lg mb-2 text-[#e9e4d8]">Party creation</h3>
        <p>
          You should build each party member according to who you currently have or potentially expect to have in a
          campaign. Most of it is self explanatory, but some other factors include "rider dice," which effectively
          means damage dice from other sources that regularly "ride" on standard attacks. Such examples may include
          sneak attacks, booming blade, hex, hunter's mark, etc. Resources are finite abilities such as spells, rage,
          action surge, battle maneuvers, etc. Alongside each of these, you can attach an expected value to be gained
          from using the resource, number of uses, reset rest, and timing. Timing represents how the resource is
          treated:
        </p>
        <ul className="list-disc pl-5 space-y-2 mt-2">
          <li>
            <b>Burst:</b> flat bonus damage on top of expected regular attack damage. Similar to a rider dice but now
            on a resource. So, a superiority dice resource for a battle master with an expected value of 7.5 and a
            timing of "burst" will be computed as 7.5 additional damage when the resource is expended.
          </li>
          <li>
            <b>Ongoing:</b> one use and it's applied across every subsequent turn. A rage with a value of 3 will only
            need one use and add 3 damage across all subsequent turns.
          </li>
        </ul>
        <p className="mt-2">
          Spells work similarly, but you can attach custom spells made in the Spell Library tab with special effects.
          Some resources, such as spells, replace actions; this can be toggled so that the damage is either attached
          to a standard attack or treated as its own action. Right now you can only select one spell per level. This
          is just to simplify, as there is no way to know what spells a player will choose to cast against a monster.
          I considered allowing multiple spells to be selected and auto selecting the spell that counters the
          monsters the best, but it would be a mismodeling, as the player cannot know a monster's vulnerabilities and
          resistances prior to trying. The selected spell can be changed as necessary when planning encounters.
        </p>
      </Panel>

      <Panel className="p-5">
        <h3 className="font-display font-bold text-lg mb-2 text-[#e9e4d8]">Monsters</h3>
        <p>
          Monsters are built similarly to players without resources, instead having innate spell casting and
          save-based attacks. There is also the option to make a monster a boss, giving it legendary resistances and
          legendary actions. Legendary actions function similarly to resources, but uses should instead be treated as
          how many times you may expect the boss to use the move in a single encounter. For special attacks (spell
          casting, saves, legendary), you can input an expected number of uses per encounter. This will automatically
          choose either the expected number or the predicted number of rounds, whichever is lower. If you want a
          monster to use the special move every turn, set the number very high.
        </p>
      </Panel>

      <Panel className="p-5">
        <h3 className="font-display font-bold text-lg mb-2 text-[#e9e4d8]">Adventuring Day</h3>
        <p>
          Start by defining the party's current status - maybe they're not all starting fresh for whatever reasons.
        </p>
        <p className="mt-2">Add an encounter.</p>
        <ul className="list-disc pl-5 space-y-2 mt-2">
          <li>Select what monsters and qualities of each you would like to be present.</li>
          <li>
            You can see the predicted difficulty and how many rounds it is expected to take for the players to kill
            all monsters or the monsters to kill ONE player.
          </li>
          <li>
            The predicted outcome and resources spent are then shown under each player. Then, if another encounter
            occurs, these values will carry over. You can edit this live during session and see how the future
            encounters you have planned may change depending on how well or poorly the party performs, and balance
            accordingly.
          </li>
        </ul>
      </Panel>

      <Panel className="p-5">
        <h3 className="font-display font-bold text-lg mb-2 text-[#e9e4d8]">Rest</h3>
        <p>
          Add a short or long rest between encounters. For short rests, you can decide how many Hit Dice a person may
          use. For long rests, it auto-fills all stats.
        </p>
      </Panel>

      <Panel className="p-5">
        <h3 className="font-display font-bold text-lg mb-2 text-[#e9e4d8]">Notes</h3>
        <ul className="list-disc pl-5 space-y-1.5">
          <li>This project solely uses 2014 D&amp;D 5e rules.</li>
          <li>The community DPR data this project calibrates against is "The Optimists' Guide to D&amp;D 5E Damage by Class."</li>
          <li>No feats are available but can be factored in using rider dice or resources as appropriate.</li>
          <li>Multi-monster-group encounters blend resistances and damage-type mix across groups by HP/DPR share, rather than simulating optimal focus fire.</li>
          <li>Incoming monster damage is spread across the party by average share, adjusted per-character by their own AC/saves/resistances, rather than simulating focus fire on the squishiest target.</li>
          <li>Legendary Resistance converts a limited number of the party's failed saves against that monster into automatic successes each encounter (the real 5e rule), reducing the expected damage from save-based spells - it only affects saving throws, not spell attack rolls or a character's own at-will/ongoing damage.</li>
        </ul>
      </Panel>
    </div>
  );
}
