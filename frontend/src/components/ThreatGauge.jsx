import React from "react";
import { Badge } from "./ui.jsx";

export function ThreatGauge({ roundsToKillMonsters, roundsToDropPC, roundsAssumed }) {
  const noThreat = roundsToDropPC >= 999;
  const cantWin = roundsToKillMonsters >= 999;
  const cap = Math.max(Math.min(roundsToKillMonsters, 50), Math.min(roundsToDropPC, 50), roundsAssumed, 1) * 1.15;
  const pW = cantWin ? 100 : Math.min(100, (roundsToKillMonsters / cap) * 100);
  const mW = noThreat ? 6 : Math.min(100, (roundsToDropPC / cap) * 100);
  const partyWinsClearly = !cantWin && (noThreat || roundsToKillMonsters <= roundsToDropPC - 1);
  const tooClose = !cantWin && !noThreat && Math.abs(roundsToKillMonsters - roundsToDropPC) <= 1;
  const dangerous = cantWin || (!noThreat && roundsToKillMonsters > roundsToDropPC);

  return (
    <div className="space-y-2.5">
      <div>
        <div className="flex justify-between text-[10.5px] text-[#8b93a7] mb-1">
          <span>Party drops all monsters</span>
          <span className="font-mono">{cantWin ? "never (0 eff. DPR)" : `${roundsToKillMonsters.toFixed(1)} rounds`}</span>
        </div>
        <div className="h-2 bg-[#141821] rounded-full overflow-hidden">
          <div className="h-full bg-[#c9a15a] rounded-full transition-all" style={{ width: `${pW}%` }} />
        </div>
      </div>
      <div>
        <div className="flex justify-between text-[10.5px] text-[#8b93a7] mb-1">
          <span>Monsters drop a PC</span>
          <span className="font-mono">{noThreat ? "no real threat" : `${roundsToDropPC.toFixed(1)} rounds`}</span>
        </div>
        <div className="h-2 bg-[#141821] rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all ${dangerous ? "bg-[#b3452c]" : "bg-[#5c8a5c]"}`} style={{ width: `${mW}%` }} />
        </div>
      </div>
      <div className="pt-1">
        {partyWinsClearly && <Badge tone="good">Comfortable margin</Badge>}
        {!partyWinsClearly && tooClose && <Badge tone="warn">Razor's edge</Badge>}
        {dangerous && <Badge tone="danger">Monsters likely win the race</Badge>}
      </div>
    </div>
  );
}
