# The War Table

A D&D 5e (2014 rules) encounter planner that treats party members and
monsters as fully custom builds, not lookups, and simulates a whole
adventuring day of resource attrition, not just one isolated fight.

Given a party (class, subclass, feats, magic items, known spells) and a
bestiary of hand-built monsters (attacks, resistances, legendary actions),
it answers the question a flat XP-budget calculator can't: *given what's
already been spent two fights ago, how much trouble is this encounter
actually going to be?*

## Why this exists

Two things are true about encounter balance in 5e:

1. The DMG's XP-budget math is a genuinely useful, well-documented starting
   point (and this project implements it faithfully: 2014 thresholds, the
   monster-count multiplier, all of it).
2. It's also famously blind to action economy, damage-type resistances,
   and, most importantly for planning a whole session, how depleted the
   party's spell slots and other resources already are by the third fight.

This project runs both: the classic XP-budget label, and a from-first-
principles "rounds to kill" simulation that actually accounts for hit
chance, crits, feats, subclass features, real spell damage (with
upcasting), and monster resistances, carried across a full day of
encounters and rests.

## Architecture

In development, the React dev server and Flask run as two processes (Vite
proxies `/api` to Flask). In the packaged Docker image, `npm run build`
runs once and Flask serves the resulting static files directly - one
process, one port, one thing to deploy:

```
┌─────────────────────┐        JSON over HTTP        ┌──────────────────────────┐
│   React frontend     │ ───────────────────────────▶ │   Flask backend          │
│  (Vite, Tailwind)    │ ◀─────────────────────────── │                          │
│                      │                               │  app/engine/  (pure      │
│  - Party / Bestiary  │                               │   Python, no I/O; the    │
│    / Day builders    │                               │   actual game math)      │
│  - Renders whatever  │                               │  app/api/     (routes)   │
│    the backend       │                               │  app/models.py (SQLA)    │
│    computes          │                               │  serves frontend/dist    │
└─────────────────────┘                               └──────────────┬───────────┘
        (dev: :5173)               (prod: same origin)                │
                                                                SQLite / Postgres
                                                              (saved campaigns)
```

The frontend holds **no game-rules knowledge**. Class lists, subclasses,
feats, spells, CR seed numbers, and every damage calculation live in
`backend/app/engine/` and are either fetched via `/api/reference-data` or
computed by `/api/simulate`. This keeps the rules logic in one place,
in a language with straightforward unit testing, instead of duplicated
(and inevitably drifting) across a JS/Python split.

### `app/engine/`: the part worth reading

This is a pure-Python package with **no Flask and no database imports**,
every function takes plain dicts and returns plain dicts, which is what
makes the 89-test suite in `backend/tests/` possible without spinning up a
web server or a database for most of it.

| Module | Responsibility |
|---|---|
| `dice_math.py` | Hit/save-chance and expected-damage probability math |
| `damage_types.py` | Resistance/vulnerability/immunity resolution |
| `classes_data.py` | Class & **subclass** progressions, resource templates, feats |
| `spells.py` | SRD damage spell data + upcasting math |
| `character.py` | A character's build → typed damage components |
| `monster.py` | A monster's build → typed damage components (incl. legendary actions) |
| `xp_budget.py` | 2014 DMG difficulty thresholds |
| `simulator.py` | Runs a full day: encounters, rests, HP/resource carry-over |

## What makes this different from a DPR spreadsheet

- **Subclass actually gates mechanics.** Only a Battle Master gets
  Superiority Dice; only an Eldritch Knight or Arcane Trickster gets
  bonus spellcasting grafted onto a martial class. Subclasses calibrated
  against ["The Optimists' Guide to D&D 5E Damage by
  Class"](https://docs.google.com/spreadsheets/d/1JIrEV1RFv6yxWEdqG6zP3z-ZONDTacquGyqYj8G-CdE)
  (a public community DPR spreadsheet) get a flat signature-feature bonus;
  everything else honestly defaults to 0 rather than a guessed number.
- **Spells are real spells.** ~30 SRD damage spells with upcasting, not a
  flat "average spell damage" placeholder. Pick Fireball and a
  fire-resistant monster in your Bestiary visibly reduces its expected damage.
- **Monsters are built, not looked up.** Every stat block (attacks, damage
  types, resistances, save-based AoEs, legendary actions) is hand-built.
  CR is only ever an optional starting-point seed.
- **A whole day, not one fight.** HP and resource pools (spell slots, Rage,
  Ki, Superiority Dice, each correctly tagged for short- vs. long-rest
  recovery) carry across encounters and rests you lay out in sequence.

See `docs/schema.md` for the exact data shapes, and the in-app "How this
works" tab for the documented approximations (multi-monster resistance
blending, single-round AoE approximation, etc.), this project would rather
tell you where it cuts corners than hide it.

## Tech stack

- **Backend:** Python, Flask, SQLAlchemy, pytest
- **Frontend:** React, Vite, Tailwind CSS
- **Data:** SQLite by default (swap `DATABASE_URL` for Postgres in production)
- **CI/CD:** GitHub Actions (backend test suite, frontend build check, Docker image build)
- **Containerization:** a single combined Docker image - Flask serves the built frontend directly, so the whole app is one process on one port

## Giving this to friends who don't want to install anything

The whole app - frontend and backend - runs as **one container on one
port**, which makes this pretty easy:

### Option A: deploy it once, share a link (recommended)

This is the version where your friends do nothing except open a URL.

1. Push this repo to your own GitHub account.
2. Go to [render.com](https://render.com), sign up (no credit card needed
   for the free tier), click **New → Blueprint**, and point it at your repo.
   Render reads `render.yaml` and sets everything up automatically.
3. Click **Apply**. After a few minutes you'll have a URL like
   `https://dnd-encounter-planner.onrender.com`.
4. Send that URL to your friends. That's it - no installs, no terminal, no Docker.

Free-tier caveat: the service sleeps after 15 minutes of no traffic, so the
first request after a quiet period takes ~30-60 seconds to wake up (it's
working, just warming up). Fine for a group testing it out; upgrade to a
paid Render plan (or Railway/Fly.io, same Dockerfile works there too) if you
want it always-on.

### Option B: run it yourself, share your local network

If you'd rather not put it on the public internet, run it on your own
machine and have friends on the same Wi-Fi hit your local IP:

```bash
docker compose up --build
```

Then find your machine's local IP (e.g. `ipconfig` on Windows, `ifconfig`
or `ip addr` on Mac/Linux) and share `http://<your-ip>:8080` with friends on
the same network. Only requires Docker Desktop installed on *your* machine
- nothing on theirs.

### Option C: local dev, no Docker at all

For actually working on the code:

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py                      # http://localhost:5000

# frontend (separate terminal)
cd frontend
npm install
npm run dev                        # http://localhost:5173, proxies /api to :5000
```

### Running the tests

```bash
cd backend
pytest -v
```

170 tests covering the dice/hit-chance math, resistance resolution, class
and subclass gating, spell upcasting, and full-day simulation scenarios
(HP carrying across fights, short- vs. long-rest resource recovery,
monster resistances discounting party damage, legendary action warnings),
plus API-level tests for every route.

## Repository layout

```
backend/
  app/
    engine/          pure game-math library (see table above)
    api/              Flask blueprints: campaigns (CRUD), reference (game data), simulate
    models.py          SQLAlchemy Campaign model
  tests/               170 tests across 9 files
frontend/
  src/
    components/        one file per UI concern (CharacterCard, MonsterCard, EncounterCard, ...)
    api/client.js       the only place that talks to the backend
    utils/factories.js  default object shapes for new characters/monsters/encounters
docs/
  schema.md            the JSON contract between frontend and backend
Dockerfile             combined image: builds the frontend, then Flask serves it
render.yaml             one-click deploy config (see "Giving this to friends" above)
```

## Known limitations

This is documented in depth in the app's own "How this works" tab, but
briefly: incoming damage is spread across the party by average share rather
than simulating focus-fire; multi-monster-group encounters blend
resistances by HP/DPR share rather than modeling optimal target selection;
and several AoE/multi-round spells are approximated as single-target,
single-round expected damage. None of these are hidden; the goal is a
tool that's honest about its own approximations.

## License

MIT. See [LICENSE](LICENSE).
