import { Plus } from "lucide-react";
import React from "react";
import { newCharacter } from "../utils/factories.js";
import { CharacterCard } from "./CharacterCard.jsx";

export function PartyTab({ party, setParty, referenceData, customSpells }) {
  const updateChar = (id, patch) => setParty((p) => p.map((c) => (c.id === id ? { ...c, ...patch } : c)));
  const removeChar = (id) => setParty((p) => p.filter((c) => c.id !== id));
  const addChar = () => setParty((p) => [...p, newCharacter()]);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-sm text-[#8b93a7] max-w-2xl">
          Build the party once. Attack math (hit chance, crits, damage types, subclass features, known spells)
          is computed by the backend against whatever you build in the Bestiary. Nothing here is locked to a single
          assumed AC or a fixed monster source.
        </p>
        <button onClick={addChar} className="flex items-center gap-1.5 bg-[#c9a15a] text-[#14171f] font-semibold rounded-sm px-3 py-2 text-sm hover:bg-[#d8b06c]">
          <Plus size={15} /> Add character
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        {party.map((c) => (
          <CharacterCard key={c.id} c={c} referenceData={referenceData} customSpells={customSpells} onChange={(patch) => updateChar(c.id, patch)} onRemove={() => removeChar(c.id)} />
        ))}
      </div>
    </div>
  );
}
