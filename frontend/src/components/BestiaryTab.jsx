import { Plus } from "lucide-react";
import React from "react";
import { newMonster } from "../utils/factories.js";
import { MonsterCard } from "./MonsterCard.jsx";

export function BestiaryTab({ bestiary, setBestiary, referenceData, customSpells }) {
  const updateMonster = (id, patch) => setBestiary((b) => b.map((m) => (m.id === id ? { ...m, ...patch } : m)));
  const removeMonster = (id) => setBestiary((b) => b.filter((m) => m.id !== id));
  const addMonster = () => setBestiary((b) => [...b, newMonster()]);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-sm text-[#8b93a7] max-w-2xl">
          Build monsters the same way you build characters: their own attacks (with damage types), resistances/vulnerabilities/immunities,
          innate spellcasting, and legendary actions for bosses. A CR seed is available purely as an optional numeric starting point.
        </p>
        <button onClick={addMonster} className="flex items-center gap-1.5 bg-[#c9a15a] text-[#14171f] font-semibold rounded-sm px-3 py-2 text-sm hover:bg-[#d8b06c]">
          <Plus size={15} /> New monster
        </button>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        {bestiary.map((m) => (
          <MonsterCard key={m.id} m={m} referenceData={referenceData} customSpells={customSpells} onChange={(patch) => updateMonster(m.id, patch)} onRemove={() => removeMonster(m.id)} />
        ))}
      </div>
    </div>
  );
}
