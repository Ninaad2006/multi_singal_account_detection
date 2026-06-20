# ─────────────────────────────────────────────
#  display.py  —  CLI rendering / pretty-print
#
#  Mirrors the cricket predictor display module.
# ─────────────────────────────────────────────

from data import DRIVER_STATS, CONSTRUCTOR_STATS, CIRCUIT_INFO, CIRCUITS, FALLBACK_SCHEDULE
from api  import RacePrediction

# accuracy imported lazily to avoid circular deps

# ── ANSI helpers ──────────────────────────────────────────────────────────────
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_YELLOW = "\033[93m"
_CYAN   = "\033[96m"
_GREEN  = "\033[92m"
_RED    = "\033[91m"
_GREY   = "\033[90m"
_WHITE  = "\033[97m"
_MAGENTA= "\033[95m"

_CONF_COLOR = {
    "High":   _GREEN,
    "Medium": _YELLOW,
    "Low":    _RED,
}

PODIUM_MEDAL = {1: "🥇", 2: "🥈", 3: "🥉"}


# ── Shared helpers ────────────────────────────────────────────────────────────

def _divider() -> None:
    print(f"\n  {_GREY}{'─' * 62}{_RESET}")


def _section(label: str, text: str) -> None:
    print(f"\n  {_CYAN}{_BOLD}{label}{_RESET}")
    words, line = text.split(), ""
    for word in words:
        if len(line) + len(word) + 1 > 72:
            print(f"    {line}")
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        print(f"    {line}")


def _prob_bar(label: str, pct: int, color: str = _YELLOW, width: int = 28) -> None:
    filled = round(pct / 100 * width)
    bar = color + "█" * filled + _GREY + "░" * (width - filled) + _RESET
    print(f"  {label:<32} {bar}  {_BOLD}{pct}%{_RESET}")


def _accuracy_bar(pct: float, width: int = 20) -> str:
    filled = round(pct / 100 * width)
    return _GREEN + "█" * filled + _GREY + "░" * (width - filled) + _RESET


def _form_str(recent_form: list[str]) -> str:
    parts = []
    for r in recent_form:
        if r == "P1":
            parts.append(_GREEN + r + _RESET)
        elif r.startswith("P") and int(r[1:]) <= 3:
            parts.append(_CYAN + r + _RESET)
        elif r == "DNF":
            parts.append(_RED + r + _RESET)
        else:
            parts.append(_GREY + r + _RESET)
    return "  ".join(parts)


# ── Driver preview ────────────────────────────────────────────────────────────

def print_driver_preview(driver: str, role: str = "") -> None:
    """Print a compact stat card for one driver."""
    d = DRIVER_STATS[driver]
    c = CONSTRUCTOR_STATS.get(d.team)
    role_tag = f"  [{role}]" if role else ""

    print(f"\n{_BOLD}{_YELLOW}{driver}{role_tag}{_RESET}  {_GREY}#{d.number} · {d.team}{_RESET}")
    print(f"  {'Championships':<22} {d.championships}")
    print(f"  {'Career Wins':<22} {d.career_wins}")
    print(f"  {'Career Poles':<22} {d.career_poles}")
    print(f"  {'Avg Qualifying':<22} P{d.avg_qualifying_pos}")
    print(f"  {'Avg Race Finish':<22} P{d.avg_race_pos}")
    print(f"  {'DNF Rate':<22} {d.dnf_rate:.0%}")
    print(f"  {'Wet Weather':<22} {d.wet_weather_rating}/10")
    print(f"  {'Overtaking':<22} {d.overtaking_rating}/10")
    print(f"  {'Recent Form':<22} {_form_str(d.recent_form)}")
    print(f"  {'Strengths':<22} {', '.join(d.strengths)}")
    if c:
        print(f"  {'Team Reliability':<22} {c.reliability_score}/10")
        print(f"  {'Avg Pit Stop':<22} {c.avg_pit_stop_ms} ms")
        print(f"  {'Power Unit':<22} {c.power_unit_supplier}")


# ── Circuit preview ───────────────────────────────────────────────────────────

def print_circuit_preview(circuit: str) -> None:
    """Print a compact circuit info card."""
    ci = CIRCUIT_INFO[circuit]
    print(f"\n{_BOLD}{_MAGENTA}CIRCUIT: {circuit}{_RESET}")
    print(f"  {ci.city}, {ci.country}  |  {ci.circuit_type}  |  {ci.laps} laps × {ci.lap_length_km} km")
    print(f"  {'DRS Zones':<22} {ci.drs_zones}")
    print(f"  {'High Speed':<22} {ci.high_speed_pct:.0%} of lap")
    print(f"  {'Overtaking':<22} {ci.overtaking_difficulty} difficulty")
    print(f"  {'Characteristics':<22} {', '.join(ci.characteristics)}")


# ── Prediction result card ────────────────────────────────────────────────────

def print_race_prediction(
    driver_a: str,
    driver_b: str,
    circuit: str,
    pred: RacePrediction,
) -> None:
    """Pretty-print the full race prediction card."""
    conf_color = _CONF_COLOR.get(pred.confidence, _WHITE)
    upset_tag  = f"  {_RED}{_BOLD}⚡ UPSET ALERT{_RESET}" if pred.upset_alert else ""

    _divider()
    print(f"  {_BOLD}{_CYAN}GROQ AI RACE PREDICTION  |  Formula 1{_RESET}")
    print(f"  Circuit:    {_MAGENTA}{circuit}{_RESET}")
    print(f"  Confidence: {conf_color}{_BOLD}{pred.confidence}{_RESET}{upset_tag}")
    _divider()

    print(f"\n  {_BOLD}PREDICTED RACE WINNER{_RESET}")
    print(f"  {_BOLD}{_YELLOW}🏆  {pred.winner}{_RESET}  {_GREY}({pred.winner_team}){_RESET}")
    print()

    _prob_bar(f"  {pred.winner} (Win chance)", pred.winner_win_pct, _YELLOW)
    _prob_bar(f"  Field (someone else wins)", 100 - pred.winner_win_pct, _GREY)

    print(f"\n  {_BOLD}PREDICTED PODIUM{_RESET}")
    for i, drv in enumerate(pred.podium[:3], 1):
        medal = PODIUM_MEDAL.get(i, "")
        color = [_YELLOW, _WHITE, _GREY][i - 1]
        print(f"  {medal}  {color}{_BOLD}P{i}{_RESET}  {drv}")

    print(f"\n  {_BOLD}POLE POSITION{_RESET}")
    print(f"  ⏱️   {_CYAN}{pred.pole_prediction}{_RESET}")

    print(f"\n  {_BOLD}STRATEGY CALL{_RESET}")
    print(f"  🔧  {pred.strategy_prediction}")

    print()
    _section("KEY FACTOR",        pred.key_factor)
    _section("CIRCUIT FIT",       pred.circuit_analysis)
    _section("CURRENT FORM",      pred.form_analysis)
    _section("DRIVER TO WATCH",   pred.driver_to_watch)
    _divider()
    _section("RACE PREVIEW",      pred.preview)
    _divider()


# ── Upcoming races ────────────────────────────────────────────────────────────

def print_upcoming(upcoming) -> None:
    """Print upcoming F1 race schedule."""
    print(f"\n{_BOLD}{_CYAN}UPCOMING RACES  —  {_RESET}{_GREY}2025 FIA Formula One World Championship{_RESET}")
    _divider()

    if upcoming:
        source = "FastF1"
        items  = [(r["name"], r.get("date", ""), r.get("country", "")) for r in upcoming[:8]]
    else:
        source = "Fallback schedule"
        items  = [(name, label, "") for name, label in FALLBACK_SCHEDULE]

    print(f"  {_GREY}Source: {source}{_RESET}\n")
    for i, (name, date, country) in enumerate(items, 1):
        country_tag = f"  {_GREY}({country}){_RESET}" if country else ""
        print(f"  {_GREY}{i:>2}.{_RESET}  {_WHITE}{name}{_RESET}{country_tag}  {_GREY}{date}{_RESET}")
    _divider()


# ── Driver + circuit selectors ────────────────────────────────────────────────

def prompt_driver_selection() -> tuple:
    """Interactively pick two drivers to compare."""
    from data import DRIVERS
    print(f"\n{_BOLD}{_YELLOW}SELECT DRIVERS{_RESET}")
    for i, d in enumerate(DRIVERS, 1):
        team = DRIVER_STATS[d].team
        print(f"  {i:>2}. {d}  {_GREY}({team}){_RESET}")

    def pick(role: str, exclude: str = "") -> str:
        while True:
            raw = input(f"\n  Enter {role} driver number: ").strip()
            if not raw.isdigit() or not (1 <= int(raw) <= len(DRIVERS)):
                print(f"  {_RED}Invalid — enter 1–{len(DRIVERS)}.{_RESET}")
                continue
            chosen = DRIVERS[int(raw) - 1]
            if chosen == exclude:
                print(f"  {_RED}Must be different from the other driver.{_RESET}")
                continue
            return chosen

    driver_a = pick("Driver A")
    driver_b = pick("Driver B", exclude=driver_a)
    return driver_a, driver_b


def prompt_circuit_selection() -> str:
    """Interactively pick a circuit."""
    print(f"\n{_BOLD}{_MAGENTA}SELECT CIRCUIT{_RESET}")
    for i, c in enumerate(CIRCUITS, 1):
        ci = CIRCUIT_INFO[c]
        print(f"  {i:>2}. {c}  {_GREY}({ci.city}, {ci.country}){_RESET}")

    while True:
        raw = input(f"\n  Enter circuit number: ").strip()
        if not raw.isdigit() or not (1 <= int(raw) <= len(CIRCUITS)):
            print(f"  {_RED}Invalid — enter 1–{len(CIRCUITS)}.{_RESET}")
            continue
        return CIRCUITS[int(raw) - 1]


# ── Accuracy display ──────────────────────────────────────────────────────────

def print_accuracy_stats() -> None:
    """Print full accuracy report."""
    import accuracy as acc
    stats = acc.get_stats()

    print(f"\n{_BOLD}{_CYAN}PREDICTION ACCURACY REPORT  —  F1{_RESET}")
    _divider()

    if stats["resolved"] == 0:
        print(f"  {_GREY}No resolved predictions yet.{_RESET}")
        print(f"  Total logged: {stats['total']}  |  Pending: {stats['pending']}")
        _divider()
        return

    pct   = stats["overall_pct"]
    color = _GREEN if pct >= 60 else (_YELLOW if pct >= 45 else _RED)
    print(f"  {'Winner accuracy':<26} {color}{_BOLD}{pct}%{_RESET}  ({stats['correct']}/{stats['resolved']} correct)")
    if stats["pole_pct"]:
        pp = stats["pole_pct"]
        pc = _GREEN if pp >= 60 else (_YELLOW if pp >= 45 else _RED)
        print(f"  {'Pole accuracy':<26} {pc}{pp}%{_RESET}")
    print(f"  {'Total logged':<26} {stats['total']}")
    print(f"  {'Pending results':<26} {stats['pending']}")

    print(f"\n  {_BOLD}By Confidence Level{_RESET}")
    for level in ("High", "Medium", "Low"):
        d = stats["by_confidence"][level]
        if d["total"] == 0:
            continue
        c   = _CONF_COLOR.get(level, _WHITE)
        bar = _accuracy_bar(d["pct"])
        print(f"  {c}{level:<8}{_RESET}  {bar}  {d['pct']}%  ({d['correct']}/{d['total']})")

    if stats["by_driver"]:
        print(f"\n  {_BOLD}By Predicted Winner{_RESET}")
        for drv, d in sorted(stats["by_driver"].items(), key=lambda x: x[1]["pct"], reverse=True):
            bar = _accuracy_bar(d["pct"])
            print(f"  {_WHITE}{drv:<28}{_RESET}  {bar}  {d['pct']}%  ({d['correct']}/{d['predicted']})")

    if stats["by_circuit"]:
        print(f"\n  {_BOLD}By Circuit{_RESET}")
        for circ, d in sorted(stats["by_circuit"].items(), key=lambda x: x[1]["pct"], reverse=True):
            bar = _accuracy_bar(d["pct"])
            print(f"  {_MAGENTA}{circ:<36}{_RESET}  {d['pct']}%  ({d['correct']}/{d['predicted']})")

    _divider()


def print_pending_predictions() -> None:
    """List all predictions awaiting a result."""
    import accuracy as acc
    pending = acc.list_pending()

    print(f"\n{_BOLD}{_CYAN}PENDING PREDICTIONS{_RESET}")
    _divider()

    if not pending:
        print(f"  {_GREEN}All predictions have been resolved!{_RESET}")
        _divider()
        return

    for r in pending:
        print(
            f"  {_GREY}[{r['id']}]{_RESET}  "
            f"{r['timestamp'][:10]}  "
            f"{_MAGENTA}{r['circuit'][:30]}{_RESET}  "
            f"->  {_YELLOW}predicted: {r['predicted_winner']}{_RESET}  "
            f"({r['confidence']} confidence)"
        )
    _divider()
    print(f"  {_GREY}Use option 3 in the menu to record actual results.{_RESET}\n")


def prompt_record_result() -> None:
    """Interactive prompt to enter the actual race winner."""
    import accuracy as acc
    pending = acc.list_pending()

    if not pending:
        print(f"\n  {_GREEN}No pending predictions to resolve.{_RESET}")
        return

    print_pending_predictions()

    pred_id = input("  Enter prediction ID to update (or Enter to cancel): ").strip()
    if not pred_id:
        return

    match = next((r for r in pending if r["id"] == pred_id), None)
    if not match:
        print(f"  {_RED}ID not found.{_RESET}")
        return

    drivers = [match["driver_a"], match["driver_b"]]
    print(f"\n  Match: {drivers[0]} vs {drivers[1]}")
    print(f"    1. {drivers[0]}")
    print(f"    2. {drivers[1]}")
    print(f"    3. Neither (someone else won)")

    raw = input("  Who actually won? (1/2/3): ").strip()
    if raw in ("1", "2"):
        actual_winner = drivers[int(raw) - 1]
    elif raw == "3":
        actual_winner = input("  Enter the actual winner's name: ").strip()
    else:
        print(f"  {_RED}Invalid input.{_RESET}")
        return

    pole_input = input("  Who took pole? (Enter to skip): ").strip()
    acc.record_result(pred_id, actual_winner, actual_pole=pole_input)

    correct = actual_winner == match["predicted_winner"]
    icon    = f"{_GREEN}CORRECT ✓{_RESET}" if correct else f"{_RED}WRONG ✗{_RESET}"
    print(f"\n  Result recorded. Winner prediction was {icon}.")
    print(f"  Predicted: {match['predicted_winner']}  |  Actual: {actual_winner}\n")
