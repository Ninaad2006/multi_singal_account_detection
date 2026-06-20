# ─────────────────────────────────────────────
#  data.py  —  Static driver & constructor stats + circuit list
#
#  Live lap/qualifying data is fetched via FastF1 in api.py.
#  This file holds baseline/historical stats used when live
#  data is unavailable or to supplement the LLM prompt.
# ─────────────────────────────────────────────

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class DriverStats:
    team: str
    nationality: str
    number: int
    championships: int
    career_wins: int
    career_poles: int
    career_podiums: int
    avg_qualifying_pos: float   # 2024 season average
    avg_race_pos: float         # 2024 season average
    dnf_rate: float             # fraction 0.0–1.0
    wet_weather_rating: int     # 1–10
    overtaking_rating: int      # 1–10
    recent_form: List[str]      # last 5 results: "P1","P2",…,"DNF"
    strengths: List[str]


@dataclass
class ConstructorStats:
    shortname: str
    color: str                  # hex for display
    championships: int
    season_wins: int            # 2024
    season_poles: int           # 2024
    avg_pit_stop_ms: int        # milliseconds
    reliability_score: float    # 0–10
    downforce_level: str        # "Low" | "Medium" | "High"
    power_unit_supplier: str
    strengths: List[str]


# ── Drivers ───────────────────────────────────────────────────────────────────

DRIVER_STATS: Dict[str, DriverStats] = {
    "Max Verstappen": DriverStats(
        team="Red Bull Racing", nationality="Dutch", number=1,
        championships=4, career_wins=61, career_poles=40, career_podiums=110,
        avg_qualifying_pos=1.9, avg_race_pos=1.8, dnf_rate=0.07,
        wet_weather_rating=10, overtaking_rating=10,
        recent_form=["P1","P1","P2","P1","DNF"],
        strengths=["Tyre management","Wet weather","Wheel-to-wheel racing","Setup feedback"],
    ),
    "Sergio Perez": DriverStats(
        team="Red Bull Racing", nationality="Mexican", number=11,
        championships=0, career_wins=7, career_poles=3, career_podiums=42,
        avg_qualifying_pos=5.2, avg_race_pos=4.1, dnf_rate=0.12,
        wet_weather_rating=7, overtaking_rating=8,
        recent_form=["P4","P3","P5","P6","P3"],
        strengths=["Race management","Long stints","Tyre preservation","Street circuits"],
    ),
    "Lewis Hamilton": DriverStats(
        team="Ferrari", nationality="British", number=44,
        championships=7, career_wins=103, career_poles=104, career_podiums=197,
        avg_qualifying_pos=3.1, avg_race_pos=3.4, dnf_rate=0.08,
        wet_weather_rating=10, overtaking_rating=9,
        recent_form=["P2","P4","P1","P3","P5"],
        strengths=["Wet weather","Lap 1 instinct","Tyre management","Adaptability"],
    ),
    "Charles Leclerc": DriverStats(
        team="Ferrari", nationality="Monegasque", number=16,
        championships=0, career_wins=8, career_poles=24, career_podiums=40,
        avg_qualifying_pos=2.8, avg_race_pos=3.9, dnf_rate=0.14,
        wet_weather_rating=8, overtaking_rating=8,
        recent_form=["P3","P1","P3","P2","P4"],
        strengths=["One-lap pace","Street circuits","Qualifying","Raw speed"],
    ),
    "Lando Norris": DriverStats(
        team="McLaren", nationality="British", number=4,
        championships=0, career_wins=4, career_poles=6, career_podiums=28,
        avg_qualifying_pos=3.5, avg_race_pos=3.2, dnf_rate=0.09,
        wet_weather_rating=9, overtaking_rating=8,
        recent_form=["P2","P2","P1","P4","P2"],
        strengths=["Qualifying pace","Consistency","Wet weather","Media lap records"],
    ),
    "Oscar Piastri": DriverStats(
        team="McLaren", nationality="Australian", number=81,
        championships=0, career_wins=2, career_poles=1, career_podiums=12,
        avg_qualifying_pos=4.1, avg_race_pos=3.8, dnf_rate=0.06,
        wet_weather_rating=7, overtaking_rating=7,
        recent_form=["P3","P5","P2","P1","P3"],
        strengths=["Tyre management","Consistent pace","Learning curve","Race craft"],
    ),
    "Carlos Sainz": DriverStats(
        team="Williams", nationality="Spanish", number=55,
        championships=0, career_wins=3, career_poles=5, career_podiums=23,
        avg_qualifying_pos=4.0, avg_race_pos=4.5, dnf_rate=0.10,
        wet_weather_rating=8, overtaking_rating=8,
        recent_form=["P4","P6","P4","P5","P4"],
        strengths=["Race craft","Tyre management","Consistency","Street circuits"],
    ),
    "George Russell": DriverStats(
        team="Mercedes", nationality="British", number=63,
        championships=0, career_wins=2, career_poles=3, career_podiums=15,
        avg_qualifying_pos=3.9, avg_race_pos=4.3, dnf_rate=0.08,
        wet_weather_rating=8, overtaking_rating=7,
        recent_form=["P5","P3","P5","P3","P6"],
        strengths=["Qualifying","Race starts","Consistency","Setup understanding"],
    ),
    "Fernando Alonso": DriverStats(
        team="Aston Martin", nationality="Spanish", number=14,
        championships=2, career_wins=32, career_poles=22, career_podiums=106,
        avg_qualifying_pos=6.5, avg_race_pos=6.1, dnf_rate=0.09,
        wet_weather_rating=10, overtaking_rating=10,
        recent_form=["P6","P7","P6","P8","P5"],
        strengths=["Wet weather","Tyre management","Strategy","Experience"],
    ),
    "Lance Stroll": DriverStats(
        team="Aston Martin", nationality="Canadian", number=18,
        championships=0, career_wins=0, career_poles=1, career_podiums=3,
        avg_qualifying_pos=9.2, avg_race_pos=8.5, dnf_rate=0.14,
        wet_weather_rating=7, overtaking_rating=6,
        recent_form=["P8","P9","P10","P7","P9"],
        strengths=["Street circuits","Race starts","Tyre warm-up","Improving late in races"],
    ),
    "Nico Hulkenberg": DriverStats(
        team="Sauber", nationality="German", number=27,
        championships=0, career_wins=0, career_poles=1, career_podiums=0,
        avg_qualifying_pos=8.1, avg_race_pos=9.2, dnf_rate=0.10,
        wet_weather_rating=8, overtaking_rating=7,
        recent_form=["P9","P10","P8","P11","P10"],
        strengths=["Qualifying","Tyre management","Clean racing","Consistency"],
    ),
    "Yuki Tsunoda": DriverStats(
        team="Red Bull Racing", nationality="Japanese", number=22,
        championships=0, career_wins=0, career_poles=0, career_podiums=0,
        avg_qualifying_pos=7.8, avg_race_pos=8.1, dnf_rate=0.15,
        wet_weather_rating=7, overtaking_rating=7,
        recent_form=["P7","P8","P9","P6","P8"],
        strengths=["Aggressive style","Qualifying laps","Improvement trajectory","Low-speed corners"],
    ),
    "Pierre Gasly": DriverStats(
        team="Alpine", nationality="French", number=10,
        championships=0, career_wins=1, career_poles=0, career_podiums=3,
        avg_qualifying_pos=9.0, avg_race_pos=10.2, dnf_rate=0.13,
        wet_weather_rating=7, overtaking_rating=7,
        recent_form=["P10","P11","P12","P9","P11"],
        strengths=["Race starts","Tyre management","Defensive driving","Street circuits"],
    ),
    "Esteban Ocon": DriverStats(
        team="Haas", nationality="French", number=31,
        championships=0, career_wins=1, career_poles=0, career_podiums=3,
        avg_qualifying_pos=10.1, avg_race_pos=10.8, dnf_rate=0.14,
        wet_weather_rating=7, overtaking_rating=6,
        recent_form=["P11","P12","P10","P13","P12"],
        strengths=["Strategy","Consistency","Wet weather","Mid-race pace"],
    ),
    "Alexander Albon": DriverStats(
        team="Williams", nationality="Thai-British", number=23,
        championships=0, career_wins=0, career_poles=0, career_podiums=2,
        avg_qualifying_pos=11.2, avg_race_pos=11.5, dnf_rate=0.12,
        wet_weather_rating=7, overtaking_rating=7,
        recent_form=["P12","P13","P11","P12","P13"],
        strengths=["Points-scoring from midfield","Tyre management","Wheel-to-wheel"],
    ),
    "Kevin Magnussen": DriverStats(
        team="Haas", nationality="Danish", number=20,
        championships=0, career_wins=0, career_poles=0, career_podiums=1,
        avg_qualifying_pos=12.0, avg_race_pos=12.5, dnf_rate=0.16,
        wet_weather_rating=7, overtaking_rating=7,
        recent_form=["P13","P14","P13","P11","P14"],
        strengths=["Aggressive defending","Race starts","Midfield battles"],
    ),
    "Valtteri Bottas": DriverStats(
        team="Sauber", nationality="Finnish", number=77,
        championships=0, career_wins=10, career_poles=20, career_podiums=67,
        avg_qualifying_pos=13.5, avg_race_pos=13.2, dnf_rate=0.10,
        wet_weather_rating=8, overtaking_rating=7,
        recent_form=["P14","P15","P14","P15","P15"],
        strengths=["Qualifying","Smooth driving","Tyre management"],
    ),
    "Zhou Guanyu": DriverStats(
        team="Sauber", nationality="Chinese", number=24,
        championships=0, career_wins=0, career_poles=0, career_podiums=0,
        avg_qualifying_pos=14.2, avg_race_pos=14.0, dnf_rate=0.12,
        wet_weather_rating=6, overtaking_rating=6,
        recent_form=["P15","P14","P15","P16","P16"],
        strengths=["Consistency","First stint pace","Low-speed corners"],
    ),
    "Oliver Bearman": DriverStats(
        team="Haas", nationality="British", number=87,
        championships=0, career_wins=0, career_poles=0, career_podiums=0,
        avg_qualifying_pos=13.0, avg_race_pos=13.5, dnf_rate=0.10,
        wet_weather_rating=6, overtaking_rating=6,
        recent_form=["P12","P13","P14","P13","P14"],
        strengths=["Raw speed","Rookie adaptability","Qualifying"],
    ),
    "Isack Hadjar": DriverStats(
        team="Racing Bulls", nationality="French", number=6,
        championships=0, career_wins=0, career_poles=0, career_podiums=0,
        avg_qualifying_pos=13.5, avg_race_pos=14.2, dnf_rate=0.12,
        wet_weather_rating=6, overtaking_rating=6,
        recent_form=["P14","P15","P13","P14","P15"],
        strengths=["Qualifying","Rookieseason pace","High-speed circuits"],
    ),
}

DRIVERS: List[str] = list(DRIVER_STATS.keys())


# ── Constructors ──────────────────────────────────────────────────────────────

CONSTRUCTOR_STATS: Dict[str, ConstructorStats] = {
    "Red Bull Racing": ConstructorStats(
        shortname="RBR", color="#3671C6",
        championships=6, season_wins=9, season_poles=8,
        avg_pit_stop_ms=2320, reliability_score=8.5,
        downforce_level="High", power_unit_supplier="Honda RBPT",
        strengths=["Aerodynamic efficiency","Pit stop speed","Race strategy","Downforce package"],
    ),
    "Ferrari": ConstructorStats(
        shortname="FER", color="#E8002D",
        championships=16, season_wins=5, season_poles=7,
        avg_pit_stop_ms=2480, reliability_score=8.0,
        downforce_level="High", power_unit_supplier="Ferrari",
        strengths=["Power unit","Qualifying pace","Tifosi motivation","Tyre warm-up"],
    ),
    "McLaren": ConstructorStats(
        shortname="MCL", color="#FF8000",
        championships=8, season_wins=6, season_poles=4,
        avg_pit_stop_ms=2350, reliability_score=9.0,
        downforce_level="High", power_unit_supplier="Mercedes",
        strengths=["2024 car pace","Consistency","Pit stop execution","Driver line-up"],
    ),
    "Mercedes": ConstructorStats(
        shortname="MER", color="#27F4D2",
        championships=8, season_wins=2, season_poles=3,
        avg_pit_stop_ms=2400, reliability_score=9.2,
        downforce_level="Medium", power_unit_supplier="Mercedes",
        strengths=["Power unit","Reliability","Race pace","Strategic calls"],
    ),
    "Aston Martin": ConstructorStats(
        shortname="AMR", color="#358C75",
        championships=0, season_wins=0, season_poles=0,
        avg_pit_stop_ms=2550, reliability_score=8.0,
        downforce_level="Medium", power_unit_supplier="Mercedes",
        strengths=["Alonso experience","Mid-race strategy","Tyre conservation"],
    ),
    "Alpine": ConstructorStats(
        shortname="ALP", color="#0093CC",
        championships=2, season_wins=0, season_poles=0,
        avg_pit_stop_ms=2700, reliability_score=7.0,
        downforce_level="Medium", power_unit_supplier="Renault",
        strengths=["Street circuits","Strategy gambles","Low-fuel pace"],
    ),
    "Haas": ConstructorStats(
        shortname="HAS", color="#B6BABD",
        championships=0, season_wins=0, season_poles=0,
        avg_pit_stop_ms=2620, reliability_score=7.5,
        downforce_level="Low", power_unit_supplier="Ferrari",
        strengths=["Aggressive strategy","Ferrari power unit","Midfield competitiveness"],
    ),
    "Williams": ConstructorStats(
        shortname="WIL", color="#64C4FF",
        championships=7, season_wins=0, season_poles=0,
        avg_pit_stop_ms=2680, reliability_score=7.8,
        downforce_level="Low", power_unit_supplier="Mercedes",
        strengths=["High-speed straights","Sainz experience","Development trajectory"],
    ),
    "Racing Bulls": ConstructorStats(
        shortname="RBU", color="#6692FF",
        championships=0, season_wins=0, season_poles=0,
        avg_pit_stop_ms=2590, reliability_score=7.5,
        downforce_level="Medium", power_unit_supplier="Honda RBPT",
        strengths=["Young driver development","Street circuits","Red Bull philosophy"],
    ),
    "Sauber": ConstructorStats(
        shortname="SAU", color="#52E252",
        championships=0, season_wins=0, season_poles=0,
        avg_pit_stop_ms=2800, reliability_score=6.5,
        downforce_level="Low", power_unit_supplier="Ferrari",
        strengths=["Strategy","Improving reliability","Hulkenberg experience"],
    ),
}

CONSTRUCTORS: List[str] = list(CONSTRUCTOR_STATS.keys())


# ── Circuits ──────────────────────────────────────────────────────────────────

@dataclass
class CircuitInfo:
    country: str
    city: str
    lap_length_km: float
    laps: int
    circuit_type: str       # "Street" | "Permanent" | "Mixed"
    high_speed_pct: float   # fraction of lap at high speed
    overtaking_difficulty: str  # "Low" | "Medium" | "High"
    drs_zones: int
    characteristics: List[str]


CIRCUIT_INFO: Dict[str, CircuitInfo] = {
    "Bahrain International Circuit": CircuitInfo(
        country="Bahrain", city="Sakhir",
        lap_length_km=5.412, laps=57, circuit_type="Permanent",
        high_speed_pct=0.55, overtaking_difficulty="Low", drs_zones=3,
        characteristics=["Tyre degradation","Night race","Long straights","Dusty off-line"],
    ),
    "Jeddah Corniche Circuit": CircuitInfo(
        country="Saudi Arabia", city="Jeddah",
        lap_length_km=6.174, laps=50, circuit_type="Street",
        high_speed_pct=0.80, overtaking_difficulty="Medium", drs_zones=3,
        characteristics=["Fastest street circuit","Walls close","High average speed","Night race"],
    ),
    "Albert Park Circuit": CircuitInfo(
        country="Australia", city="Melbourne",
        lap_length_km=5.278, laps=58, circuit_type="Mixed",
        high_speed_pct=0.60, overtaking_difficulty="Medium", drs_zones=4,
        characteristics=["Flowing layout","Bumpy surface","Safety car risk","Mixed weather"],
    ),
    "Suzuka International Racing Course": CircuitInfo(
        country="Japan", city="Suzuka",
        lap_length_km=5.807, laps=53, circuit_type="Permanent",
        high_speed_pct=0.65, overtaking_difficulty="High", drs_zones=1,
        characteristics=["Figure-of-eight","Technical corners","Low overtaking","Driver's circuit"],
    ),
    "Shanghai International Circuit": CircuitInfo(
        country="China", city="Shanghai",
        lap_length_km=5.451, laps=56, circuit_type="Permanent",
        high_speed_pct=0.55, overtaking_difficulty="Low", drs_zones=2,
        characteristics=["Long back straight","Heavy braking zones","Abrasive surface","Sprint weekend"],
    ),
    "Miami International Autodrome": CircuitInfo(
        country="USA", city="Miami",
        lap_length_km=5.412, laps=57, circuit_type="Street",
        high_speed_pct=0.65, overtaking_difficulty="Medium", drs_zones=3,
        characteristics=["Street circuit","Hot conditions","Sprint weekend","High-speed sections"],
    ),
    "Autodromo Enzo e Dino Ferrari": CircuitInfo(
        country="Italy", city="Imola",
        lap_length_km=4.909, laps=63, circuit_type="Permanent",
        high_speed_pct=0.55, overtaking_difficulty="High", drs_zones=2,
        characteristics=["Narrow layout","Low overtaking","Qualifying critical","Gravel traps"],
    ),
    "Circuit de Monaco": CircuitInfo(
        country="Monaco", city="Monte Carlo",
        lap_length_km=3.337, laps=78, circuit_type="Street",
        high_speed_pct=0.30, overtaking_difficulty="High", drs_zones=1,
        characteristics=["Narrowest circuit","Impossible to overtake","Qualifying decisive","Prestige"],
    ),
    "Circuit de Barcelona-Catalunya": CircuitInfo(
        country="Spain", city="Barcelona",
        lap_length_km=4.657, laps=66, circuit_type="Permanent",
        high_speed_pct=0.55, overtaking_difficulty="High", drs_zones=2,
        characteristics=["Tyre critical","Known circuit","Low overtaking","High-speed corners"],
    ),
    "Circuit Gilles Villeneuve": CircuitInfo(
        country="Canada", city="Montreal",
        lap_length_km=4.361, laps=70, circuit_type="Street",
        high_speed_pct=0.50, overtaking_difficulty="Low", drs_zones=2,
        characteristics=["Wall of Champions","Safety car circuit","Stop-start layout","Good overtaking"],
    ),
    "Red Bull Ring": CircuitInfo(
        country="Austria", city="Spielberg",
        lap_length_km=4.318, laps=71, circuit_type="Permanent",
        high_speed_pct=0.65, overtaking_difficulty="Low", drs_zones=3,
        characteristics=["Short lap","High altitude","Sprint weekend","Wheel-to-wheel racing"],
    ),
    "Silverstone Circuit": CircuitInfo(
        country="UK", city="Northampton",
        lap_length_km=5.891, laps=52, circuit_type="Permanent",
        high_speed_pct=0.70, overtaking_difficulty="Medium", drs_zones=2,
        characteristics=["High-speed corners","Changeable weather","Home GP","Copse & Maggotts"],
    ),
    "Hungaroring": CircuitInfo(
        country="Hungary", city="Budapest",
        lap_length_km=4.381, laps=70, circuit_type="Permanent",
        high_speed_pct=0.35, overtaking_difficulty="High", drs_zones=2,
        characteristics=["Monaco without walls","Slow twisty","Tyre management","Strategy key"],
    ),
    "Circuit de Spa-Francorchamps": CircuitInfo(
        country="Belgium", city="Spa",
        lap_length_km=7.004, laps=44, circuit_type="Permanent",
        high_speed_pct=0.70, overtaking_difficulty="Low", drs_zones=2,
        characteristics=["Longest circuit","Eau Rouge","Changeable weather","High speed"],
    ),
    "Circuit Zandvoort": CircuitInfo(
        country="Netherlands", city="Zandvoort",
        lap_length_km=4.259, laps=72, circuit_type="Permanent",
        high_speed_pct=0.55, overtaking_difficulty="High", drs_zones=2,
        characteristics=["Banking turns","Narrow circuit","Verstappen home","Low overtaking"],
    ),
    "Autodromo Nazionale Monza": CircuitInfo(
        country="Italy", city="Monza",
        lap_length_km=5.793, laps=53, circuit_type="Permanent",
        high_speed_pct=0.85, overtaking_difficulty="Low", drs_zones=2,
        characteristics=["Temple of Speed","Low downforce","Drag reduction key","Slipstreaming"],
    ),
    "Baku City Circuit": CircuitInfo(
        country="Azerbaijan", city="Baku",
        lap_length_km=6.003, laps=51, circuit_type="Street",
        high_speed_pct=0.60, overtaking_difficulty="Low", drs_zones=2,
        characteristics=["Long straight","Castle section","Safety car risk","Sprint weekend"],
    ),
    "Marina Bay Street Circuit": CircuitInfo(
        country="Singapore", city="Marina Bay",
        lap_length_km=4.940, laps=62, circuit_type="Street",
        high_speed_pct=0.30, overtaking_difficulty="High", drs_zones=3,
        characteristics=["Night race","Humid conditions","Strategy critical","Safety cars"],
    ),
    "Circuit of the Americas": CircuitInfo(
        country="USA", city="Austin",
        lap_length_km=5.513, laps=56, circuit_type="Permanent",
        high_speed_pct=0.60, overtaking_difficulty="Low", drs_zones=2,
        characteristics=["Flowing layout","Sprint weekend","Good overtaking","Technical section"],
    ),
    "Autodromo Hermanos Rodriguez": CircuitInfo(
        country="Mexico", city="Mexico City",
        lap_length_km=4.304, laps=71, circuit_type="Permanent",
        high_speed_pct=0.55, overtaking_difficulty="Low", drs_zones=3,
        characteristics=["High altitude","Stadium section","Engine stress","Thin air"],
    ),
    "Autodromo Jose Carlos Pace": CircuitInfo(
        country="Brazil", city="São Paulo",
        lap_length_km=4.309, laps=71, circuit_type="Permanent",
        high_speed_pct=0.60, overtaking_difficulty="Low", drs_zones=2,
        characteristics=["Interlagos","Sprint weekend","Changeable weather","Good racing"],
    ),
    "Las Vegas Strip Circuit": CircuitInfo(
        country="USA", city="Las Vegas",
        lap_length_km=6.201, laps=50, circuit_type="Street",
        high_speed_pct=0.75, overtaking_difficulty="Low", drs_zones=2,
        characteristics=["Night race","Long straights","Cold temperatures","Street circuit"],
    ),
    "Lusail International Circuit": CircuitInfo(
        country="Qatar", city="Lusail",
        lap_length_km=5.380, laps=57, circuit_type="Permanent",
        high_speed_pct=0.65, overtaking_difficulty="Medium", drs_zones=2,
        characteristics=["Night race","Hot humid","Sprint weekend","High-speed flowing"],
    ),
    "Yas Marina Circuit": CircuitInfo(
        country="UAE", city="Abu Dhabi",
        lap_length_km=5.281, laps=58, circuit_type="Permanent",
        high_speed_pct=0.60, overtaking_difficulty="Low", drs_zones=3,
        characteristics=["Season finale","Twilight to night","Modern layout","Good overtaking"],
    ),
}

CIRCUITS: List[str] = list(CIRCUIT_INFO.keys())


# ── Fallback race schedule (used when live API unavailable) ───────────────────

FALLBACK_SCHEDULE = [
    ("Bahrain International Circuit",    "Round 1"),
    ("Jeddah Corniche Circuit",          "Round 2"),
    ("Albert Park Circuit",              "Round 3"),
    ("Suzuka International Racing Course","Round 4"),
    ("Shanghai International Circuit",   "Round 5"),
    ("Miami International Autodrome",    "Round 6"),
    ("Circuit de Monaco",                "Round 7"),
    ("Circuit Gilles Villeneuve",        "Round 8"),
]
