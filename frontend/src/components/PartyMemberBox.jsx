import { ChevronDown, ChevronUp, User } from "lucide-react";
import React from "react";
import { NumberInput } from "./ui.jsx";

/** A small rectangular card representing one party member: collapsed shows
 * just an icon, name, and a one-line status; expanded reveals whatever the
 * caller passes as children. Used identically for the day's starting
 * conditions and for each encounter's party state, so the whole day reads
 * as one consistent visual language instead of different-looking panels. */
export function PartyMemberBox({ character, expanded, onToggle, statusLine, statusTone = "text-[#8b93a7]", children }) {
  return (
    <div className="w-28 shrink-0">
      <button
        onClick={onToggle}
        className={`w-full flex flex-col items-center gap-0.5 p-2 rounded-sm border transition-colors ${
          expanded ? "bg-[#242b3d] border-[#c9a15a]/50" : "bg-[#141821] border-[#333c52] hover:border-[#5c6478]"
        }`}
      >
        <User size={24} className="text-[#8b93a7]" />
        <span className="text-[10.5px] text-[#c7cbd6] truncate w-full text-center">{character.name}</span>
        <span className={`text-[9.5px] font-mono2 ${statusTone}`}>{statusLine}</span>
        {expanded ? <ChevronUp size={10} className="text-[#5c6478]" /> : <ChevronDown size={10} className="text-[#5c6478]" />}
      </button>
      {expanded && <div className="mt-1 p-2 bg-[#141821] border border-[#333c52] rounded-sm text-[10.5px] space-y-1.5">{children}</div>}
    </div>
  );
}

/** Green/amber/red HP-fraction coloring, shared everywhere a status line shows HP. */
export function hpTone(hp, max) {
  if (!max) return "text-[#8b93a7]";
  return hp / max < 0.3 ? "text-[#e08065]" : hp / max < 0.6 ? "text-[#e0a860]" : "text-[#8fbf8f]";
}

/** One line inside an expanded PartyMemberBox: a label, a small secondary
 * caption, and a number input - the shape every HP/resource row shares
 * (starting conditions, resource spend, ...), just with different labels,
 * captions, and bounds. */
export function MiniStatRow({ label, secondary, value, onChange, min = 0, max }) {
  return (
    <div className="flex items-center gap-1">
      <span className="flex-1 truncate text-[#8b93a7]" title={label}>
        {label}
      </span>
      <span className="font-mono2 text-[#5c6478] text-[9px]">{secondary}</span>
      <NumberInput value={value} min={min} max={max} onChange={onChange} className="!py-0.5 !text-[10.5px] w-12" />
    </div>
  );
}
