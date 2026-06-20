# ─────────────────────────────────────────────
#  api.py  —  External API calls
#             · FastF1  (live lap / qualifying data)
#             · Groq    (LLM race prediction)
# ─────────────────────────────────────────────

import json
import requests
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple

from config import (
    GROQ_API_KEY, GROQ_MODEL, GROQ_ENDPOINT,
    FASTF1_CACHE_DIR, RECENT_RACES_COUNT,
    MAX_TOKENS, TEMPERATURE, CURRENT_SEASON,
)
from data import DRIVER_STATS, CONSTRUCTOR_STATS, CIRCUIT_INFO, DRIVERS, FALLBACK_SCHEDULE


# ── Prediction result ─────────────────────────────────────────────────────────

@dataclass
class RacePrediction:
    winner: str                     # predicted race winner (driver name)
    podium: List[str]               # top 3 predicted
    pole_prediction: str            # predicted pole sitter
    winner_team: str
    winner_win_pct: int             # probability 0–100
    key_factor: str
    circuit_analysis: str
    form_analysis: str
    strategy_prediction: str        # e.g. "One-stop medium-hard"
    driver_to_watch: str
    preview: str                    # 2–3 sentence journalist preview
    upset_alert: bool
    confidence: str                 # "Low" | "Medium" | "High"


# ── FastF1 helpers ────────────────────────────────────────────────────────────

def _init_fastf1() -> bool:
    """
    Try to import and enable FastF1 cache.
    Returns True if successful, False if not installed.
    """
    try:
        import fastf1
        import os
        os.makedirs(FASTF1_CACHE_DIR, exist_ok=True)
        fastf1.Cache.enable_cache(FASTF1_CACHE_DIR)
        return True
    except ImportError:
        return False


def fetch_driver_season_stats(driver_name: str, season: int = CURRENT_SEASON) -> Optional[Dict]:
    """
    Pull a driver's season stats from FastF1:
    average qualifying position, average race finish, fastest lap count.
    Returns None if FastF1 is unavailable or data missing.
    """
    if not _init_fastf1():
        return None
    try:
        import fastf1
        schedule = fastf1.get_event_schedule(season, include_testing=False)
        results = []
        for _, event in schedule.iterrows():
            try:
                session = fastf1.get_session(season, event["EventName"], "R")
                session.load(laps=False, telemetry=False, weather=False, messages=False)
                r = session.results
                driver_row = r[r["FullName"].str.contains(driver_name.split()[-1], na=False)]
                if not driver_row.empty:
                    pos = driver_row.iloc[0]["Position"]
                    if pos and str(pos).isdigit():
                        results.append(int(pos))
            except Exception:
                continue
        if not results:
            return None
        return {
            "avg_race_pos": round(sum(results) / len(results), 2),
            "races_completed": len(results),
            "best_finish": min(results),
        }
    except Exception:
        return None


def fetch_qualifying_results(circuit_name: str, season: int = CURRENT_SEASON) -> Optional[List[Dict]]:
    """
    Fetch the most recent qualifying session results for a circuit from FastF1.
    Returns a list of {driver, team, position, q3_time} dicts, or None.
    """
    if not _init_fastf1():
        return None
    try:
        import fastf1
        session = fastf1.get_session(season, circuit_name, "Q")
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        results = session.results[["FullName", "TeamName", "Position", "Q3"]].dropna(subset=["FullName"])
        out = []
        for _, row in results.iterrows():
            out.append({
                "driver":   str(row["FullName"]),
                "team":     str(row["TeamName"]),
                "position": int(row["Position"]) if row["Position"] else 99,
                "q3_time":  str(row["Q3"]) if row["Q3"] else "N/A",
            })
        return out[:10]  # top 10
    except Exception:
        return None


def fetch_race_results(circuit_name: str, season: int = CURRENT_SEASON) -> Optional[List[Dict]]:
    """
    Fetch race results for a given circuit from the current/last season.
    Returns list of {driver, team, position, fastest_lap, points} dicts, or None.
    """
    if not _init_fastf1():
        return None
    try:
        import fastf1
        session = fastf1.get_session(season, circuit_name, "R")
        session.load(laps=False, telemetry=False, weather=False, messages=False)
        results = session.results[["FullName", "TeamName", "Position", "Points", "Status"]]
        out = []
        for _, row in results.iterrows():
            out.append({
                "driver":   str(row["FullName"]),
                "team":     str(row["TeamName"]),
                "position": int(row["Position"]) if str(row["Position"]).isdigit() else 99,
                "points":   float(row["Points"]) if row["Points"] else 0,
                "status":   str(row["Status"]),
            })
        return sorted(out, key=lambda x: x["position"])[:10]
    except Exception:
        return None


def fetch_upcoming_races() -> Optional[List[Dict]]:
    """
    Return upcoming/recent F1 races from FastF1 schedule.
    Returns list of {name, date, circuit} dicts, or None.
    """
    if not _init_fastf1():
        return None
    try:
        import fastf1
        from datetime import datetime
        schedule = fastf1.get_event_schedule(CURRENT_SEASON, include_testing=False)
        now = datetime.now()
        upcoming = []
        for _, event in schedule.iterrows():
            try:
                race_date = event["EventDate"]
                if hasattr(race_date, "to_pydatetime"):
                    race_date = race_date.to_pydatetime()
                upcoming.append({
                    "name":    str(event["EventName"]),
                    "country": str(event["Country"]),
                    "date":    str(event["EventDate"])[:10],
                    "circuit": str(event.get("Location", "")),
                    "round":   int(event["RoundNumber"]),
                })
            except Exception:
                continue
        return sorted(upcoming, key=lambda x: x["round"])
    except Exception:
        return None


# ── Groq race prediction ──────────────────────────────────────────────────────

def fetch_race_prediction(
    driver_a: str,
    driver_b: str,
    circuit: str,
    qualifying_results: Optional[List[Dict]] = None,
    live_form: Optional[Dict] = None,
) -> RacePrediction:
    """
    Send driver stats + circuit info to Groq and return a structured RacePrediction.
    Raises ValueError on bad input, requests.HTTPError on API failure.
    """
    if driver_a not in DRIVER_STATS:
        raise ValueError(f"Unknown driver: {driver_a!r}")
    if driver_b not in DRIVER_STATS:
        raise ValueError(f"Unknown driver: {driver_b!r}")
    if driver_a == driver_b:
        raise ValueError("Select two different drivers to compare.")
    if circuit not in CIRCUIT_INFO:
        raise ValueError(f"Unknown circuit: {circuit!r}")

    prompt = _build_prompt(driver_a, driver_b, circuit, qualifying_results, live_form)

    response = requests.post(
        GROQ_ENDPOINT,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
        },
        json={
            "model":       GROQ_MODEL,
            "max_tokens":  MAX_TOKENS,
            "temperature": TEMPERATURE,
            "messages": [
                {
                    "role":    "system",
                    "content": (
                        "You are a Formula 1 race analyst with deep knowledge of circuits, "
                        "driver styles, team strategies, and race dynamics. "
                        "Always respond with valid JSON only — no markdown, no backticks."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        },
        timeout=30,
    )
    response.raise_for_status()

    data    = response.json()
    raw     = data["choices"][0]["message"]["content"]
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    parsed  = json.loads(cleaned)

    return RacePrediction(
        winner             = parsed["winner"],
        podium             = parsed["podium"],
        pole_prediction    = parsed["polePrediction"],
        winner_team        = parsed["winnerTeam"],
        winner_win_pct     = int(parsed["winnerWinPct"]),
        key_factor         = parsed["keyFactor"],
        circuit_analysis   = parsed["circuitAnalysis"],
        form_analysis      = parsed["formAnalysis"],
        strategy_prediction= parsed["strategyPrediction"],
        driver_to_watch    = parsed["driverToWatch"],
        preview            = parsed["preview"],
        upset_alert        = bool(parsed["upsetAlert"]),
        confidence         = parsed["confidence"],
    )


def _build_prompt(
    driver_a: str,
    driver_b: str,
    circuit: str,
    qualifying_results: Optional[List[Dict]],
    live_form: Optional[Dict],
) -> str:
    da = DRIVER_STATS[driver_a]
    db = DRIVER_STATS[driver_b]
    ca = CONSTRUCTOR_STATS.get(da.team, None)
    cb = CONSTRUCTOR_STATS.get(db.team, None)
    ci = CIRCUIT_INFO[circuit]

    def driver_block(name: str, d: DriverStats, c: Optional["ConstructorStats"]) -> str:
        block = (
            f"\nDRIVER: {name}\n"
            f"- Team:              {d.team}\n"
            f"- Championships:     {d.championships}\n"
            f"- Career Wins:       {d.career_wins}\n"
            f"- Career Poles:      {d.career_poles}\n"
            f"- Avg Qualifying:    P{d.avg_qualifying_pos}\n"
            f"- Avg Race Finish:   P{d.avg_race_pos}\n"
            f"- DNF Rate:          {d.dnf_rate:.0%}\n"
            f"- Wet Weather:       {d.wet_weather_rating}/10\n"
            f"- Overtaking:        {d.overtaking_rating}/10\n"
            f"- Recent Form:       {', '.join(d.recent_form)}\n"
            f"- Strengths:         {', '.join(d.strengths)}\n"
        )
        if c:
            block += (
                f"- Team Reliability:  {c.reliability_score}/10\n"
                f"- Avg Pit Stop:      {c.avg_pit_stop_ms}ms\n"
                f"- Power Unit:        {c.power_unit_supplier}\n"
                f"- Team Strengths:    {', '.join(c.strengths)}\n"
            )
        return block

    circuit_block = (
        f"\nCIRCUIT: {circuit}\n"
        f"- Country:           {ci.country}\n"
        f"- Type:              {ci.circuit_type}\n"
        f"- Lap Length:        {ci.lap_length_km} km\n"
        f"- Laps:              {ci.laps}\n"
        f"- High Speed %:      {ci.high_speed_pct:.0%}\n"
        f"- Overtaking:        {ci.overtaking_difficulty}\n"
        f"- DRS Zones:         {ci.drs_zones}\n"
        f"- Characteristics:   {', '.join(ci.characteristics)}\n"
    )

    qualifying_block = ""
    if qualifying_results:
        qualifying_block = "\nQUALIFYING (FastF1 live data):\n"
        for r in qualifying_results[:5]:
            qualifying_block += f"  P{r['position']}: {r['driver']} ({r['team']})\n"

    return (
        "You are a sharp F1 race analyst. Predict who wins this Grand Prix head-to-head "
        "based on the stats provided.\n"
        + driver_block(driver_a, da, ca)
        + driver_block(driver_b, db, cb)
        + circuit_block
        + qualifying_block
        + """
Respond ONLY with valid JSON, no markdown, no extra text:
{
  "winner": "<exact driver name>",
  "podium": ["<P1 driver>", "<P2 driver>", "<P3 driver>"],
  "polePrediction": "<driver name most likely to take pole>",
  "winnerTeam": "<winner's team name>",
  "winnerWinPct": <integer 0-100, probability this driver wins>,
  "confidence": "<Low|Medium|High>",
  "keyFactor": "<one sharp sentence on the single biggest deciding factor>",
  "circuitAnalysis": "<one sentence on how this circuit suits or hurts each driver>",
  "formAnalysis": "<one sentence comparing current form of both drivers>",
  "strategyPrediction": "<predicted tyre strategy, e.g. 'One-stop Medium-Hard'>",
  "driverToWatch": "<driver name (can be a third driver) and why they matter>",
  "preview": "<2-3 sentences of journalist-style race preview>",
  "upsetAlert": <true|false>
}"""
    )
