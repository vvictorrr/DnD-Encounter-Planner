import { Info, Plus, Trash2 } from "lucide-react";
import React, { useEffect, useState } from "react";

export const Panel = ({ children, className = "" }) => (
  <div className={`bg-[#1c212e] border border-[#333c52] rounded-sm ${className}`} style={{ backgroundColor: "#1c212e" }}>
    {children}
  </div>
);

export const Field = ({ label, children, hint }) => (
  <label className="flex flex-col gap-1 text-xs">
    <span className="text-[#8b93a7] uppercase tracking-wide font-medium flex items-center gap-1">
      {label}
      {hint && <InfoTooltip text={hint} />}
    </span>
    {children}
  </label>
);

/** A small hover-triggered "i" icon that reveals explanatory text - keeps
 * dense forms from being permanently cluttered with paragraphs of caption text. */
export function InfoTooltip({ text }) {
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-flex" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <Info size={11} className="text-[#5c6478] hover:text-[#c9a15a] cursor-help" />
      {open && (
        <span
          className="absolute z-20 left-1/2 -translate-x-1/2 top-full mt-1.5 w-56 p-2 rounded-sm border border-[#333c52] text-[10.5px] font-normal normal-case tracking-normal leading-snug shadow-lg"
          style={{ backgroundColor: "#0f1219", color: "#c7cbd6" }}
        >
          {text}
        </span>
      )}
    </span>
  );
}

// Explicit inline style fallback alongside the Tailwind classes: some
// browsers (Safari in particular) don't reliably apply arbitrary-value
// utility classes to native <input>/<select> elements, especially with
// autofill or a light OS-level color scheme in play. Setting the same
// colors via style + forcing color-scheme: dark makes this bulletproof
// regardless of browser quirks.
const baseInputStyle = { backgroundColor: "#141821", color: "#e9e4d8", colorScheme: "dark" };
const inputCls =
  "bg-[#141821] border border-[#333c52] rounded-sm px-2 py-1.5 text-[#e9e4d8] text-sm focus:outline-none focus:ring-1 focus:ring-[#c9a15a] focus:border-[#c9a15a] appearance-none min-w-0 w-full";

/**
 * A number input that behaves the way people expect: you can select-all and
 * delete to leave it blank while you type a new value, instead of it being
 * silently forced back to 0/the-old-value on every keystroke. The parent's
 * onChange only fires with a real number once you commit (blur or Enter);
 * if you leave it blank and click away, it quietly reverts to whatever it
 * was before rather than zeroing out.
 */
export function NumberInput({ value, onChange, className = "", ...rest }) {
  const [draft, setDraft] = useState(value === null || value === undefined ? "" : String(value));

  useEffect(() => {
    // Stay in sync if the value changes from outside (e.g. a resync button)
    // without clobbering what the user is actively mid-typing.
    setDraft(value === null || value === undefined ? "" : String(value));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  const commit = () => {
    if (draft === "" || draft === "-") {
      setDraft(value === null || value === undefined ? "" : String(value));
      return;
    }
    const parsed = Number(draft);
    if (Number.isNaN(parsed)) {
      setDraft(value === null || value === undefined ? "" : String(value));
      return;
    }
    if (parsed !== value) onChange({ target: { value: String(parsed) } });
  };

  return (
    <input
      type="text"
      inputMode="decimal"
      className={inputCls + " w-full " + className}
      style={baseInputStyle}
      value={draft}
      onChange={(e) => {
        const v = e.target.value;
        if (v === "" || v === "-" || /^-?\d*\.?\d*$/.test(v)) setDraft(v);
      }}
      onBlur={commit}
      onKeyDown={(e) => {
        if (e.key === "Enter") e.target.blur();
      }}
      {...rest}
    />
  );
}

export const TextInput = ({ className = "", ...props }) => (
  <input type="text" className={inputCls + " w-full " + className} style={baseInputStyle} {...props} />
);
export const Select = ({ children, className = "", ...props }) => (
  <select className={inputCls + " w-full " + className} style={baseInputStyle} {...props}>
    {children}
  </select>
);

export const Checkbox = ({ checked, onChange, label }) => (
  <label className="flex items-center gap-1.5 text-xs text-[#c7cbd6] cursor-pointer select-none">
    <input type="checkbox" checked={checked} onChange={onChange} className="accent-[#c9a15a]" />
    {label}
  </label>
);

const TONES = {
  neutral: "bg-[#242b3d] text-[#8b93a7] border-[#333c52]",
  good: "bg-[#5c8a5c]/15 text-[#8fbf8f] border-[#5c8a5c]/40",
  warn: "bg-[#c98a3a]/15 text-[#e0a860] border-[#c98a3a]/40",
  danger: "bg-[#b3452c]/15 text-[#e08065] border-[#b3452c]/40",
};

export function Badge({ tone = "neutral", children }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded-sm text-[10.5px] font-semibold uppercase tracking-wide border ${TONES[tone]}`}>
      {children}
    </span>
  );
}

/** A row of small headline stat cards (label + big value), used at the top
 * of both CharacterCard and MonsterCard - same markup, different numbers.
 * Pass `accent: true` on any one stat to give it the gold highlight color
 * instead of the default off-white. */
export function StatCardRow({ stats, className = "" }) {
  return (
    <div className={`grid grid-cols-3 gap-3 ${className}`}>
      {stats.map(({ label, value, accent, hint }) => (
        <div key={label} className="bg-[#141821] rounded-sm px-3 py-2 border border-[#333c52]">
          <div className="text-[10.5px] text-[#8b93a7] uppercase flex items-center gap-1">
            {label}
            {hint && <InfoTooltip text={hint} />}
          </div>
          <div className={`font-mono2 text-lg font-semibold ${accent ? "text-[#c9a15a]" : "text-[#e9e4d8]"}`}>{value}</div>
        </div>
      ))}
    </div>
  );
}

/** Reusable editor for resistance / vulnerability / immunity lists. */
export function DamageTypeListEditor({ list, onChange, damageTypes, tone = "neutral" }) {
  const [draftType, setDraftType] = useState(damageTypes[0]);
  const [draftMagicalOnly, setDraftMagicalOnly] = useState(false);

  const add = () => {
    if (list.some((x) => x.type === draftType)) return;
    onChange([...list, { type: draftType, magical_only: draftMagicalOnly }]);
  };
  const remove = (t) => onChange(list.filter((x) => x.type !== t));

  return (
    <div className="space-y-1.5">
      <div className="flex flex-wrap gap-1">
        {list.length === 0 && <span className="text-[10.5px] text-[#5c6478] italic">none</span>}
        {list.map((x) => (
          <span
            key={x.type}
            className={`inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-sm border ${
              tone === "danger"
                ? "bg-[#b3452c]/10 border-[#b3452c]/30 text-[#e08065]"
                : tone === "good"
                  ? "bg-[#5c8a5c]/10 border-[#5c8a5c]/30 text-[#8fbf8f]"
                  : "bg-[#242b3d] border-[#333c52] text-[#8b93a7]"
            }`}
          >
            {x.type}
            {x.magical_only ? " (nonmagical only)" : ""}
            <button onClick={() => remove(x.type)} className="hover:text-[#e08065]">
              <Trash2 size={9} />
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-1 items-center">
        <Select value={draftType} onChange={(e) => setDraftType(e.target.value)} className="!py-0.5 !text-[10.5px] w-28">
          {damageTypes.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </Select>
        <Checkbox checked={draftMagicalOnly} onChange={(e) => setDraftMagicalOnly(e.target.checked)} label="nonmagical only" />
        <button onClick={add} className="text-[10.5px] text-[#c9a15a] flex items-center gap-0.5 ml-auto">
          <Plus size={11} />
          add
        </button>
      </div>
    </div>
  );
}
