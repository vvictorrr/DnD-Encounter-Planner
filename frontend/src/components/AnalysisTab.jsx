import { HeartPulse, Skull, Sparkles } from "lucide-react";
import React from "react";
import { Badge, Panel } from "./ui.jsx";

export function AnalysisTab({ party, items, snapshots }) {
  const encounters = items.map((it, i) => ({ item: it, snap: snapshots[i] })).filter((x) => x.item.type === "encounter" && x.snap);

  if (encounters.length === 0) {
    return <Panel className="p-8 text-center text-[#8b93a7] text-sm">Add encounters in the Adventuring Day tab to see analysis.</Panel>;
  }

  return (
    <div className="space-y-6">
      <Panel className="p-4">
        <h3 className="font-display font-semibold text-base mb-3 flex items-center gap-2">
          <HeartPulse size={16} className="text-[#b3452c]" />
          HP trajectory across the day
        </h3>
        <div className="space-y-3">
          {party.map((c) => {
            const points = [c.max_hp, ...encounters.map((e) => e.snap.hp_after[c.id])];
            return (
              <div key={c.id} className="flex items-center gap-3">
                <div className="w-28 text-xs text-[#c7cbd6] truncate">{c.name}</div>
                <div className="flex-1 flex items-end gap-1 h-10">
                  {points.map((hp, i) => (
                    <div key={i} className="flex-1 bg-[#141821] rounded-sm relative h-full overflow-hidden" title={`${hp}/${c.max_hp}`}>
                      <div
                        className={`absolute bottom-0 left-0 right-0 ${hp / c.max_hp < 0.3 ? "bg-[#b3452c]" : hp / c.max_hp < 0.6 ? "bg-[#c98a3a]" : "bg-[#5c8a5c]"}`}
                        style={{ height: `${Math.max(4, (hp / c.max_hp) * 100)}%` }}
                      />
                    </div>
                  ))}
                </div>
                <div className="w-16 text-right font-mono2 text-xs text-[#8b93a7]">
                  {points[points.length - 1]}/{c.max_hp}
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex gap-1 mt-2 pl-[7.5rem] text-[9.5px] text-[#5c6478]">
          <span className="w-28" />
          {["start", ...encounters.map((e, i) => e.item.name || `E${i + 1}`)].map((l, i) => (
            <div key={i} className="flex-1 text-center truncate">
              {l}
            </div>
          ))}
        </div>
      </Panel>

      <Panel className="p-4">
        <h3 className="font-display font-semibold text-base mb-3 flex items-center gap-2">
          <Skull size={16} className="text-[#c9a15a]" />
          Encounter-by-encounter verdicts
        </h3>
        <div className="space-y-2">
          {encounters.map(({ item, snap }, i) => (
            <div key={item.id} className="flex items-center gap-3 bg-[#141821] rounded-sm px-3 py-2 border border-[#333c52]">
              <span className="font-mono2 text-xs text-[#5c6478] w-8">#{i + 1}</span>
              <span className="flex-1 text-sm">{item.name}</span>
              <Badge tone={snap.label.tone}>{snap.label.text}</Badge>
              <span className="text-[11px] font-mono2 text-[#8b93a7] w-32 text-right">{snap.rounds_to_kill_monsters.toFixed(1)} rounds to clear</span>
              <span className="text-[11px] font-mono2 text-[#8b93a7] w-32 text-right">{snap.rounds_to_drop_pc.toFixed(1)} rounds to drop PC</span>
            </div>
          ))}
        </div>
      </Panel>

      <Panel className="p-4">
        <h3 className="font-display font-semibold text-base mb-3 flex items-center gap-2">
          <Sparkles size={16} className="text-[#c9a15a]" />
          Resource depletion
        </h3>
        <div className="space-y-4">
          {party.map(
            (c) =>
              c.resources.length > 0 && (
                <div key={c.id}>
                  <div className="text-xs font-medium text-[#c7cbd6] mb-1">{c.name}</div>
                  {c.resources.map((r) => {
                    const series = encounters.map((e) => e.snap.resources_before[c.id]?.[r.name] ?? r.max);
                    return (
                      <div key={r.name} className="flex items-center gap-2 text-[10.5px] mb-1">
                        <span className="w-40 truncate text-[#8b93a7]">{r.name}</span>
                        <div className="flex-1 flex gap-1">
                          {series.map((v, i) => (
                            <div key={i} className="flex-1 bg-[#141821] h-3 rounded-sm relative overflow-hidden">
                              <div className="absolute inset-y-0 left-0 bg-[#c9a15a]/70" style={{ width: `${r.max > 0 ? (v / r.max) * 100 : 0}%` }} />
                            </div>
                          ))}
                        </div>
                        <span className="font-mono2 text-[#5c6478] w-16 text-right">
                          {series[series.length - 1]}/{r.max}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ),
          )}
        </div>
      </Panel>
    </div>
  );
}
