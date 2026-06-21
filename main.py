# ─────────────────────────────────────────────
#  main.py  —  Entry point; ties all modules together
#
#  Modules:
#    config.py   → API keys & constants
#    data.py     → Driver/constructor/circuit stats
#    api.py      → FastF1 live data + Groq LLM prediction
#    accuracy.py → Log predictions, record results, compute stats
#    display.py  → All CLI rendering
#
#  Usage:
#    python main.py                            # interactive menu
#    python main.py "Max Verstappen" "Lando Norris" "Silverstone Circuit"
#    python main.py --accuracy                 # accuracy report and exit
# ─────────────────────────────────────────────

import sys

from data    import DRIVERS, CIRCUITS
from api     import (
    fetch_race_prediction,
    fetch_qualifying_results,
    fetch_upcoming_races,
    RacePrediction,
)
from display import (
    print_driver_preview,
    print_circuit_preview,
    print_race_prediction,
    print_upcoming,
    prompt_driver_selection,
    prompt_circuit_selection,
    print_accuracy_stats,
    print_pending_predictions,
    prompt_record_result,
)
import accuracy

# ── ANSI helpers ──────────────────────────────────────────────────────────────
_BOLD   = "\033[1m"
_YELLOW = "\033[93m"
_GREEN  = "\033[92m"
_RED    = "\033[91m"
_GREY   = "\033[90m"
_RESET  = "\033[0m"


# ── 1. Predict ────────────────────────────────────────────────────────────────

def run_prediction(driver_a: str, driver_b: str, circuit: str) -> None:
    """
    Full prediction pipeline:
      preview drivers → preview circuit → call Groq → display result → log
    """
    print_driver_preview(driver_a, role="Driver A")
    print_driver_preview(driver_b, role="Driver B")
    print_circuit_preview(circuit)

    # Try to fetch FastF1 qualifying data for added context
    print(f"\n  ⏳  Loading FastF1 data…")
    qualifying = fetch_qualifying_results(circuit)
    if qualifying:
        print(f"  {_GREEN}✓  FastF1 qualifying data loaded ({len(qualifying)} results){_RESET}")
    else:
        print(f"  {_GREY}ℹ  FastF1 data unavailable — using static stats{_RESET}")

    print(f"\n  ⏳  Fetching prediction from Groq…")
    try:
        prediction = fetch_race_prediction(driver_a, driver_b, circuit, qualifying)
    except ValueError as e:
        print(f"\n  {_RED}❌  Input error:{_RESET} {e}")
        return
    except Exception as e:
        print(f"\n  {_RED}❌  API error:{_RESET} {e}")
        return

    print_race_prediction(driver_a, driver_b, circuit, prediction)

    pred_id = accuracy.log_prediction(driver_a, driver_b, circuit, prediction)
    print(f"  {_GREY}Prediction logged  [ID: {_YELLOW}{pred_id}{_GREY}]"
          f"  — record result later from menu option 3.{_RESET}\n")


# ── 2. Accuracy report ────────────────────────────────────────────────────────

def show_accuracy_report() -> None:
    stats = accuracy.get_stats()
    print(f"\n  {_GREY}Total: {stats['total']}  "
          f"| Resolved: {stats['resolved']}  "
          f"| Pending: {stats['pending']}{_RESET}")
    print_accuracy_stats()


# ── 3. Record result ──────────────────────────────────────────────────────────

def record_result() -> None:
    prompt_record_result()


# ── 4. View pending ───────────────────────────────────────────────────────────

def view_pending() -> None:
    print_pending_predictions()


# ── Main menu ─────────────────────────────────────────────────────────────────

def main_menu() -> None:
    while True:
        print(f"\n{'─' * 48}")
        print(f"  {_BOLD}{_YELLOW}🏎️   F1 RACE PREDICTOR  —  MAIN MENU{_RESET}")
        print(f"{'─' * 48}")
        print("  1.  Predict a race (Driver vs Driver)")
        print("  2.  View accuracy report")
        print("  3.  Record actual race result")
        print("  4.  View pending predictions")
        print("  5.  Exit")
        print(f"{'─' * 48}")

        choice = input("  Choose (1–5): ").strip()

        if choice == "1":
            driver_a, driver_b = prompt_driver_selection()
            circuit             = prompt_circuit_selection()
            run_prediction(driver_a, driver_b, circuit)

        elif choice == "2":
            show_accuracy_report()

        elif choice == "3":
            record_result()

        elif choice == "4":
            view_pending()

        elif choice == "5":
            print(f"\n  {_GREY}Goodbye! 🏎️{_RESET}\n")
            sys.exit(0)

        else:
            print(f"  {_RED}Invalid choice — enter 1 to 5.{_RESET}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print("\n" + "=" * 66)
    print("  🏎️   F1 RACE PREDICTOR  ·  Powered by FastF1 + Groq + LLaMA 3")
    print("=" * 66)

    args = sys.argv[1:]

    if "--accuracy" in args:
        show_accuracy_report()
        return

    # python main.py "Driver A" "Driver B" "Circuit Name"
    if len(args) >= 3:
        driver_a, driver_b, circuit = args[0], args[1], args[2]
        for drv in (driver_a, driver_b):
            if drv not in DRIVERS:
                print(f"\n  {_RED}❌  Unknown driver:{_RESET} {drv!r}")
                print(f"  Available: {', '.join(DRIVERS)}")
                sys.exit(1)
        if circuit not in CIRCUITS:
            print(f"\n  {_RED}❌  Unknown circuit:{_RESET} {circuit!r}")
            print(f"  Available: {', '.join(CIRCUITS)}")
            sys.exit(1)
        upcoming = fetch_upcoming_races()
        print_upcoming(upcoming)
        run_prediction(driver_a, driver_b, circuit)
        return

    # Default: interactive menu
    upcoming = fetch_upcoming_races()
    print_upcoming(upcoming)
    main_menu()


if __name__ == "__main__":
    main()
