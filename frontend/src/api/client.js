/**
 * Thin fetch wrapper around the Flask API. Every function here maps to
 * exactly one backend route (see backend/app/api/ and docs/schema.md) - the
 * frontend holds no game-rules knowledge of its own beyond what these calls
 * hand it.
 */
const BASE_URL = import.meta.env.VITE_API_URL || "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.error || detail;
    } catch {
      /* response wasn't JSON - keep statusText */
    }
    throw new Error(`${options.method || "GET"} ${path} failed: ${detail}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  // --- reference data (game constants live in the backend) ---
  getReferenceData: () => request("/reference-data"),
  getResourceTemplate: (cls, level, subclass) =>
    request("/reference/resource-template", {
      method: "POST",
      body: JSON.stringify({ cls, level, subclass }),
    }),
  getMonsterSeed: (cr) =>
    request("/reference/monster-seed", { method: "POST", body: JSON.stringify({ cr }) }),

  // --- simulation (stateless - runs against whatever you pass it) ---
  simulate: (party, bestiary, items, customSpells, startingHp, startingResources) =>
    request("/simulate", {
      method: "POST",
      body: JSON.stringify({
        party, bestiary, items, custom_spells: customSpells,
        starting_hp: startingHp, starting_resources: startingResources,
      }),
    }),

  // --- campaign persistence ---
  listCampaigns: () => request("/campaigns"),
  createCampaign: (data) => request("/campaigns", { method: "POST", body: JSON.stringify(data) }),
  getCampaign: (id) => request(`/campaigns/${id}`),
  updateCampaign: (id, data) => request(`/campaigns/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteCampaign: (id) => request(`/campaigns/${id}`, { method: "DELETE" }),
};
