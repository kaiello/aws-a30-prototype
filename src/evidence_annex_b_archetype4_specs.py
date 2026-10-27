"""Declarative specifications for Annex B Archetype 4 figures (cycle_waveform_plot).

Source: AWS A3.0M/A3.0:2020 (printed pp. 148–157, PDF indices 160–169).
All figure titles are cross-verified against List of Figures (printed pp. x–xi, PDF indices 10–11).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class TraceVariableSpec:
    name: str
    physical_quantity: str
    unit: Optional[str] = None
    description: str = ""


@dataclass(frozen=True)
class TemporalIntervalSpec:
    name: str
    order: int
    parent_interval: Optional[str] = None
    description: str = ""
    clause4_term: Optional[str] = None


@dataclass(frozen=True)
class WaveformParameterSpec:
    name: str
    associated_trace: str
    associated_interval: Optional[str] = None
    description: str = ""


@dataclass(frozen=True)
class CycleWaveformSpec:
    figure_id: str
    official_title: str
    short_title: str
    pages: List[Tuple[int, int]]  # (pdf_index, printed_page)
    crop_box: Tuple[float, float, float, float]  # normalized [ymin, xmin, ymax, xmax]
    time_axis: str
    traces: List[TraceVariableSpec]
    intervals: List[TemporalIntervalSpec]
    parameters: List[WaveformParameterSpec] = field(default_factory=list)
    compound_intervals: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    source_anomalies: List[Dict[str, Any]] = field(default_factory=list)
    clause4_terms: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Figure B49: Pulsation Welding Waveform (Resistance Spot Welding)
# ---------------------------------------------------------------------------
FIGURE_B49_SPEC = CycleWaveformSpec(
    figure_id="Figure B49",
    official_title="Example of a Pulsation Welding Waveform for Resistance Spot Welding",
    short_title="Pulsation Welding Waveform",
    pages=[(165, 153)],
    crop_box=(0.05, 0.05, 0.48, 0.95),
    time_axis="TIME",
    traces=[
        TraceVariableSpec(
            name="RESISTANCE WELDING CURRENT",
            physical_quantity="Electric Current",
            unit="Amperes",
            description="The current in the secondary circuit during the weld interval or weld time.",
        ),
        TraceVariableSpec(
            name="ELECTRODE FORCE",
            physical_quantity="Force",
            unit="Newtons / Pounds-force",
            description="The compressive force applied to the workpieces by the electrodes.",
        ),
    ],
    intervals=[
        TemporalIntervalSpec(
            name="SQUEEZE TIME",
            order=1,
            description="The interval between initiation of the welding cycle and first application of current.",
            clause4_term="squeeze time",
        ),
        TemporalIntervalSpec(
            name="PREHEAT TIME",
            order=2,
            description="The duration of preheat current flow.",
            clause4_term="preheat time",
        ),
        TemporalIntervalSpec(
            name="UPSLOPE TIME",
            order=3,
            description="The interval during which the welding current or power is continuously increased.",
            clause4_term="upslope time",
        ),
        TemporalIntervalSpec(
            name="WELD INTERVAL",
            order=4,
            description="The sum of heat and cool times to produce a pulsation weld.",
            clause4_term="weld interval",
        ),
        TemporalIntervalSpec(
            name="HEAT TIME",
            order=5,
            parent_interval="WELD INTERVAL",
            description="The duration of a pulse during the weld interval.",
            clause4_term="pulse time",
        ),
        TemporalIntervalSpec(
            name="COOL TIME",
            order=6,
            parent_interval="WELD INTERVAL",
            description="Any interval between squeeze time and hold time when no resistance welding current flows.",
            clause4_term="cool time",
        ),
        TemporalIntervalSpec(
            name="DOWNSLOPE TIME",
            order=7,
            description="The interval during which the welding current or power is continuously decreased.",
            clause4_term="downslope time",
        ),
        TemporalIntervalSpec(
            name="QUENCH TIME",
            order=8,
            description="The duration from the end of the weld interval or downslope time to the beginning of temper time.",
            clause4_term="quench time",
        ),
        TemporalIntervalSpec(
            name="TEMPER TIME",
            order=9,
            description="The time following quench time during which a current is passed through the weld.",
            clause4_term="temper time",
        ),
        TemporalIntervalSpec(
            name="HOLD TIME",
            order=10,
            description="The duration of force application after the last heat function has ended.",
            clause4_term="hold time",
        ),
        TemporalIntervalSpec(
            name="OFF TIME",
            order=11,
            description="The interval between welding cycles when operating in a repeat mode.",
            clause4_term="off time",
        ),
    ],
    parameters=[
        WaveformParameterSpec(
            name="PREHEAT CURRENT",
            associated_trace="RESISTANCE WELDING CURRENT",
            associated_interval="PREHEAT TIME",
            description="One or more current pulses occurring prior to and separated from welding current.",
        ),
        WaveformParameterSpec(
            name="UPSLOPE CURRENT",
            associated_trace="RESISTANCE WELDING CURRENT",
            associated_interval="UPSLOPE TIME",
            description="Continuously increasing secondary current prior to full weld current.",
        ),
        WaveformParameterSpec(
            name="WELDING CURRENT",
            associated_trace="RESISTANCE WELDING CURRENT",
            associated_interval="WELD INTERVAL",
            description="Full pulsed secondary welding current magnitude.",
        ),
        WaveformParameterSpec(
            name="DOWNSLOPE CURRENT",
            associated_trace="RESISTANCE WELDING CURRENT",
            associated_interval="DOWNSLOPE TIME",
            description="Continuously decreasing secondary current.",
        ),
        WaveformParameterSpec(
            name="TEMPER CURRENT",
            associated_trace="RESISTANCE WELDING CURRENT",
            associated_interval="TEMPER TIME",
            description="Current passed through weldment for in-situ heat treatment.",
        ),
    ],
    compound_intervals=[
        {
            "name": "POSTWELD INTERVAL",
            "description": "The duration from the end of the weld interval through the hold time.",
            "subsumes": ["QUENCH TIME", "TEMPER TIME", "HOLD TIME"],
            "clause4_term": "postweld interval",
        },
        {
            "name": "FORGE-DELAY TIME",
            "description": "The duration between a preselected point in the welding cycle and the initiation of forge force.",
            "clause4_term": "forge-delay time",
        },
        {
            "name": "WELDING CYCLE",
            "description": "The complete series of events involved in the making of a weld.",
            "clause4_term": "welding cycle",
        },
    ],
    notes=[
        "Source credit on page 153: Reproduced from AWS J1.1:2013, Specification for Resistance Welding Controls, Figure A.3.",
        "Co-located on printed p. 153 (PDF index 165) with Figure B50.",
    ],
    source_anomalies=[
        {
            "anomaly_id": "ANOMALY-B49-COLOCATION",
            "description": "Figure B49 and Figure B50 share a single printed page (p. 153, PDF index 165) with distinct vertical partitions.",
            "resolution": "Partitioned page crops: top half (0.05..0.48) for B49 and bottom half (0.48..0.95) for B50.",
        }
    ],
    clause4_terms=[
        "cool time",
        "downslope time",
        "forge-delay time",
        "hold time",
        "postweld interval",
        "preheat current",
        "preheat time",
        "pulsation welding",
        "pulse time",
        "quench time",
        "resistance spot welding",
        "squeeze time",
        "temper time",
        "upslope time",
        "weld interval",
        "weld time",
        "welding current",
        "welding cycle",
    ],
)


# ---------------------------------------------------------------------------
# Figure B50: Single-Pulse Resistance Spot Welding Waveform
# ---------------------------------------------------------------------------
FIGURE_B50_SPEC = CycleWaveformSpec(
    figure_id="Figure B50",
    official_title="Example of a Single-Pulse Resistance Spot Welding Waveform",
    short_title="Single-Pulse Resistance Spot Welding Waveform",
    pages=[(165, 153)],
    crop_box=(0.48, 0.05, 0.95, 0.95),
    time_axis="TIME",
    traces=[
        TraceVariableSpec(
            name="RESISTANCE WELDING CURRENT",
            physical_quantity="Electric Current",
            unit="Amperes",
            description="Secondary circuit current during the single pulse.",
        ),
        TraceVariableSpec(
            name="ELECTRODE FORCE",
            physical_quantity="Force",
            unit="Newtons / Pounds-force",
            description="Electrode force applied to the weldment.",
        ),
    ],
    intervals=[
        TemporalIntervalSpec(
            name="PREWELD INTERVAL",
            order=1,
            description="The elapsed time between the initiation of the squeeze time and the beginning of the weld time.",
            clause4_term="preweld interval",
        ),
        TemporalIntervalSpec(
            name="SQUEEZE TIME",
            order=2,
            description="The interval between initiation of the welding cycle and first application of current.",
            clause4_term="squeeze time",
        ),
        TemporalIntervalSpec(
            name="WELD TIME",
            order=3,
            description="The duration of time when welding current passes through workpieces during a single impulse.",
            clause4_term="weld time",
        ),
        TemporalIntervalSpec(
            name="HOLD TIME",
            order=4,
            description="The duration of force application after the single impulse ends.",
            clause4_term="hold time",
        ),
        TemporalIntervalSpec(
            name="OFF TIME",
            order=5,
            description="The interval between welding cycles when operating in a repeat mode.",
            clause4_term="off time",
        ),
    ],
    parameters=[
        WaveformParameterSpec(
            name="WELDING CURRENT",
            associated_trace="RESISTANCE WELDING CURRENT",
            associated_interval="WELD TIME",
            description="Secondary welding current level during single impulse.",
        ),
        WaveformParameterSpec(
            name="ELECTRODE FORCE",
            associated_trace="ELECTRODE FORCE",
            description="Constant or modulated electrode force applied across the single impulse cycle.",
        ),
    ],
    compound_intervals=[
        {
            "name": "WELDING CYCLE",
            "description": "The complete series of events involved in the making of a single-pulse weld.",
            "clause4_term": "welding cycle",
        }
    ],
    notes=[
        "Single-impulse welding operates with 1 continuous pulse (no heat/cool sub-intervals).",
        "Co-located on printed p. 153 (PDF index 165) below Figure B49.",
    ],
    source_anomalies=[
        {
            "anomaly_id": "ANOMALY-B50-COLOCATION",
            "description": "Figure B50 shares printed p. 153 (PDF index 165) with Figure B49.",
            "resolution": "Bounded to bottom half of PDF index 165.",
        }
    ],
    clause4_terms=[
        "off time",
        "preweld interval",
        "pulse time",
        "resistance spot welding",
        "single-impulse welding",
        "squeeze time",
        "weld time",
        "welding current",
        "welding cycle",
    ],
)


# ---------------------------------------------------------------------------
# Figure B53: Welding Cycle for Pulsed Welding
# ---------------------------------------------------------------------------
FIGURE_B53_SPEC = CycleWaveformSpec(
    figure_id="Figure B53",
    official_title="An Example of a Welding Cycle for Pulsed Welding",
    short_title="Welding Cycle for Pulsed Welding",
    pages=[(169, 157)],
    crop_box=(0.05, 0.05, 0.58, 0.95),
    time_axis="TIME",
    traces=[
        TraceVariableSpec(
            name="WELDING CURRENT",
            physical_quantity="Electric Current",
            unit="Amperes",
            description="Arc current trace including hot start, initial, pulse, and final currents.",
        ),
        TraceVariableSpec(
            name="ARC VOLTAGE",
            physical_quantity="Electric Potential",
            unit="Volts",
            description="Arc voltage across torch and workpiece.",
        ),
        TraceVariableSpec(
            name="WIRE FEED SPEED",
            physical_quantity="Linear Speed",
            unit="Inches per minute / Meters per minute",
            description="Filler metal delivery speed.",
        ),
        TraceVariableSpec(
            name="TRAVEL SPEED",
            physical_quantity="Linear Speed",
            unit="Inches per minute / Meters per minute",
            description="Linear progression speed of torch, gun, or workpiece.",
        ),
        TraceVariableSpec(
            name="SHIELDING GAS FLOW",
            physical_quantity="Flow Rate",
            unit="Cubic feet per hour / Liters per minute",
            description="Protective gas envelope flow rate.",
        ),
    ],
    intervals=[
        TemporalIntervalSpec(
            name="PREFLOW TIME",
            order=1,
            description="The time interval between start of shielding gas flow and arc starting.",
            clause4_term="preflow time",
        ),
        TemporalIntervalSpec(
            name="START TIME",
            order=2,
            description="The time interval prior to the weld time during which initial arc conditions are established.",
            clause4_term="start time",
        ),
        TemporalIntervalSpec(
            name="TRAVEL START DELAY TIME",
            order=3,
            description="The time interval from arc initiation to the start of the torch, gun, or workpiece travel.",
            clause4_term="travel start delay time",
        ),
        TemporalIntervalSpec(
            name="FILLER METAL START DELAY TIME",
            order=4,
            description="The time interval from arc initiation to the start of filler metal feeding.",
            clause4_term="filler metal start delay time",
        ),
        TemporalIntervalSpec(
            name="UPSLOPE TIME",
            order=5,
            description="The interval during which the welding current or power is continuously increased.",
            clause4_term="upslope time",
        ),
        TemporalIntervalSpec(
            name="WELD TIME",
            order=6,
            description="The time interval from end of start time or upslope to beginning of current decrease.",
            clause4_term="weld time",
        ),
        TemporalIntervalSpec(
            name="HIGH PULSE TIME",
            order=7,
            parent_interval="WELD TIME",
            description="The duration of the high pulse current.",
            clause4_term="high pulse time",
        ),
        TemporalIntervalSpec(
            name="LOW PULSE TIME",
            order=8,
            parent_interval="WELD TIME",
            description="The duration of the low current pulse.",
            clause4_term="low pulse time",
        ),
        TemporalIntervalSpec(
            name="TAPER DELAY TIME",
            order=9,
            description="The time interval after upslope during which maximum welding current is maintained before taper.",
            clause4_term="taper delay time",
        ),
        TemporalIntervalSpec(
            name="TAPER TIME",
            order=10,
            description="The time interval when current increases or decreases continuously from welding current to final taper current.",
            clause4_term="taper time",
        ),
        TemporalIntervalSpec(
            name="TRAVEL STOP DELAY TIME",
            order=11,
            description="The time interval from beginning of downslope time or crater fill time to shut-off of travel.",
            clause4_term="travel stop delay time",
        ),
        TemporalIntervalSpec(
            name="FILLER METAL STOP DELAY TIME",
            order=12,
            description="The time delay interval from beginning of downslope time to stop of filler metal feeding.",
            clause4_term="filler metal stop delay time",
        ),
        TemporalIntervalSpec(
            name="DOWNSLOPE TIME",
            order=13,
            description="The interval during which welding current or power is continuously decreased.",
            clause4_term="downslope time",
        ),
        TemporalIntervalSpec(
            name="POSTFLOW TIME",
            order=14,
            description="The time interval from current shut-off to either shielding gas or cooling water shut-off.",
            clause4_term="postflow time",
        ),
    ],
    parameters=[
        WaveformParameterSpec(
            name="HOT START CURRENT",
            associated_trace="WELDING CURRENT",
            associated_interval="START TIME",
            description="A very brief current pulse at arc initiation to stabilize the arc quickly.",
        ),
        WaveformParameterSpec(
            name="INITIAL CURRENT",
            associated_trace="WELDING CURRENT",
            associated_interval="START TIME",
            description="The current after starting, but before establishment of welding current.",
        ),
        WaveformParameterSpec(
            name="HIGH PULSE CURRENT",
            associated_trace="WELDING CURRENT",
            associated_interval="HIGH PULSE TIME",
            description="The current during high pulse time producing high heat level.",
        ),
        WaveformParameterSpec(
            name="LOW PULSE CURRENT",
            associated_trace="WELDING CURRENT",
            associated_interval="LOW PULSE TIME",
            description="The current during low pulse time producing low heat level.",
        ),
        WaveformParameterSpec(
            name="FINAL TAPER CURRENT",
            associated_trace="WELDING CURRENT",
            associated_interval="TAPER TIME",
            description="The current at the end of the taper interval prior to downslope.",
        ),
        WaveformParameterSpec(
            name="FINAL CURRENT",
            associated_trace="WELDING CURRENT",
            associated_interval="DOWNSLOPE TIME",
            description="The current after downslope but prior to current shut-off.",
        ),
    ],
    compound_intervals=[
        {
            "name": "PULSE START DELAY TIME",
            "description": "The time interval from current initiation to beginning of current pulsation.",
            "clause4_term": "pulse start delay time",
        },
        {
            "name": "WELDING CYCLE",
            "description": "The complete series of events involved in making a pulsed arc weld.",
            "clause4_term": "welding cycle",
        },
    ],
    notes=[
        "Co-located on printed p. 157 (PDF index 169) with Figure B54.",
        "Represents advanced GTAW / GMAW-P arc welding cycles with synchronized gas, wire, and travel controls.",
    ],
    source_anomalies=[
        {
            "anomaly_id": "ANOMALY-B53-COLOCATION",
            "description": "Figure B53 and Figure B54 share printed p. 157 (PDF index 169).",
            "resolution": "Partitioned page crops: top half (0.05..0.58) for B53 and bottom half (0.58..0.95) for B54.",
        }
    ],
    clause4_terms=[
        "downslope time",
        "filler metal stop delay time",
        "final current",
        "final taper current",
        "high pulse current",
        "high pulse time",
        "hot start current",
        "initial current",
        "low pulse current",
        "low pulse time",
        "postflow time",
        "preflow time",
        "pulse start delay time",
        "taper delay time",
        "taper time",
        "travel start delay time",
        "travel stop delay time",
        "upslope time",
        "weld time",
        "welding current",
        "welding cycle",
    ],
)


# ---------------------------------------------------------------------------
# Figure B54: Typical GMAW, FCAW, and SAW Welding Cycle
# ---------------------------------------------------------------------------
FIGURE_B54_SPEC = CycleWaveformSpec(
    figure_id="Figure B54",
    official_title="Typical GMAW, FCAW, and SAW Welding Cycle",
    short_title="GMAW, FCAW, and SAW Welding Cycle",
    pages=[(169, 157)],
    crop_box=(0.58, 0.05, 0.95, 0.95),
    time_axis="TIME",
    traces=[
        TraceVariableSpec(
            name="WELDING CURRENT",
            physical_quantity="Electric Current",
            unit="Amperes",
            description="Secondary arc current trace.",
        ),
        TraceVariableSpec(
            name="ARC VOLTAGE",
            physical_quantity="Electric Potential",
            unit="Volts",
            description="Arc voltage across wire and base material.",
        ),
        TraceVariableSpec(
            name="WIRE FEED SPEED",
            physical_quantity="Linear Speed",
            unit="Inches per minute",
            description="Electrode feed rate.",
        ),
        TraceVariableSpec(
            name="SHIELDING GAS FLOW",
            physical_quantity="Flow Rate",
            unit="Cubic feet per hour",
            description="Shielding gas flow rate.",
        ),
    ],
    intervals=[
        TemporalIntervalSpec(
            name="PREFLOW TIME",
            order=1,
            description="The time interval between start of shielding gas flow and arc starting.",
            clause4_term="preflow time",
        ),
        TemporalIntervalSpec(
            name="START TIME",
            order=2,
            description="The time interval prior to weld time during which arc voltage and current reach operating conditions.",
            clause4_term="start time",
        ),
        TemporalIntervalSpec(
            name="FILLER METAL START DELAY TIME",
            order=3,
            description="The time interval from arc initiation to the start of filler metal feeding.",
            clause4_term="filler metal start delay time",
        ),
        TemporalIntervalSpec(
            name="WELD TIME",
            order=4,
            description="The time interval from end of start time or upslope to beginning of crater fill time.",
            clause4_term="weld time",
        ),
        TemporalIntervalSpec(
            name="CRATER FILL TIME",
            order=5,
            description="The time interval following weld time but prior to meltback time during which arc voltage and current are controlled to fill the crater.",
            clause4_term="crater fill time",
        ),
        TemporalIntervalSpec(
            name="MELTBACK TIME",
            order=6,
            description="The time interval at the end of crater fill time to arc outage during which electrode wire burns back toward contact tip.",
            clause4_term="meltback time",
        ),
        TemporalIntervalSpec(
            name="POSTFLOW TIME",
            order=7,
            description="The time interval from current shut-off to shielding gas shut-off.",
            clause4_term="postflow time",
        ),
    ],
    parameters=[
        WaveformParameterSpec(
            name="START CURRENT",
            associated_trace="WELDING CURRENT",
            associated_interval="START TIME",
            description="The current value during the start time interval.",
        ),
        WaveformParameterSpec(
            name="START VOLTAGE",
            associated_trace="ARC VOLTAGE",
            associated_interval="START TIME",
            description="The voltage value during start time interval.",
        ),
        WaveformParameterSpec(
            name="CRATER FILL CURRENT",
            associated_trace="WELDING CURRENT",
            associated_interval="CRATER FILL TIME",
            description="The current value during crater fill time.",
        ),
        WaveformParameterSpec(
            name="CRATER FILL VOLTAGE",
            associated_trace="ARC VOLTAGE",
            associated_interval="CRATER FILL TIME",
            description="The arc voltage value during crater fill time.",
        ),
    ],
    compound_intervals=[
        {
            "name": "WELDING CYCLE",
            "description": "The complete series of events involved in making a GMAW/FCAW/SAW weld.",
            "clause4_term": "welding cycle",
        }
    ],
    notes=[
        "Co-located on printed p. 157 (PDF index 169) below Figure B53.",
    ],
    source_anomalies=[
        {
            "anomaly_id": "ANOMALY-B54-COLOCATION",
            "description": "Figure B54 shares printed p. 157 (PDF index 169) with Figure B53.",
            "resolution": "Bounded to bottom half of PDF index 169.",
        }
    ],
    clause4_terms=[
        "crater fill current",
        "crater fill time",
        "crater fill voltage",
        "filler metal start delay time",
        "meltback time",
        "postflow time",
        "preflow time",
        "start current",
        "start time",
        "weld time",
        "welding current",
        "welding cycle",
    ],
)


# ---------------------------------------------------------------------------
# Figure B44: Generalized Diagram of Inertia Friction Welding
# ---------------------------------------------------------------------------
FIGURE_B44_SPEC = CycleWaveformSpec(
    figure_id="Figure B44",
    official_title="Generalized Diagram of Inertia Friction Welding",
    short_title="Inertia Friction Welding Diagram",
    pages=[(160, 148)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    time_axis="TIME",
    traces=[
        TraceVariableSpec(
            name="ROTATIONAL SPEED",
            physical_quantity="Angular Velocity",
            unit="RPM",
            description="Flywheel deceleration profile starting at initial contact friction speed and ending at zero.",
        ),
        TraceVariableSpec(
            name="AXIAL FORCE",
            physical_quantity="Force",
            unit="Newtons / Pounds-force",
            description="Thrust force applied axially between rotating and non-rotating workpieces.",
        ),
        TraceVariableSpec(
            name="UPSET",
            physical_quantity="Length / Displacement",
            unit="Millimeters / Inches",
            description="Cumulative reduction in axial workpiece length (axial shortening).",
        ),
    ],
    intervals=[
        TemporalIntervalSpec(
            name="FRICTION PHASE",
            order=1,
            description="The interval during which rotational kinetic energy is converted to frictional heat at faying surfaces.",
            clause4_term="friction welding",
        ),
        TemporalIntervalSpec(
            name="FORGE PHASE",
            order=2,
            description="The optional phase near or at rotational arrest where elevated axial force completes the solid-state weld.",
            clause4_term="inertia friction welding",
        ),
    ],
    parameters=[
        WaveformParameterSpec(
            name="FRICTION SPEED",
            associated_trace="ROTATIONAL SPEED",
            associated_interval="FRICTION PHASE",
            description="The relative velocity of the workpieces at the time of initial contact.",
        ),
        WaveformParameterSpec(
            name="FRICTION WELDING FORCE",
            associated_trace="AXIAL FORCE",
            associated_interval="FRICTION PHASE",
            description="The compressive force applied to the faying surfaces during relative motion.",
        ),
        WaveformParameterSpec(
            name="FRICTION UPSET DISTANCE",
            associated_trace="UPSET",
            associated_interval="FRICTION PHASE",
            description="The decrease in length of workpieces during friction welding force application.",
        ),
        WaveformParameterSpec(
            name="TOTAL UPSET DISTANCE",
            associated_trace="UPSET",
            description="The total reduction in axial length of workpieces from initial contact to completion of weld.",
        ),
    ],
    compound_intervals=[
        {
            "name": "TOTAL WELDING TIME",
            "description": "Total elapsed time from initial contact until rotational arrest and force release.",
            "clause4_term": "welding cycle",
        }
    ],
    notes=[
        "Inertia friction welding uses stored kinetic energy in a flywheel.",
        "Authentic source anomaly: Page caption omits 'Figure', reading 'B44—Generalized Diagram of Inertia Friction Welding'.",
    ],
    source_anomalies=[
        {
            "anomaly_id": "ANOMALY-B44-CAPTION-OMISSION",
            "description": "Page caption on printed p. 148 (PDF index 160) lacks the word 'Figure', displaying 'B44—Generalized Diagram of Inertia Friction Welding'.",
            "resolution": "Matched against both 'Figure B44' and 'B44' in caption parser.",
        }
    ],
    clause4_terms=[
        "friction speed",
        "friction upset distance",
        "friction welding",
        "friction welding force",
        "inertia friction welding",
        "upset distance",
    ],
)


# ---------------------------------------------------------------------------
# Figure B45: Generalized Diagram of Direct Drive Friction Welding
# ---------------------------------------------------------------------------
FIGURE_B45_SPEC = CycleWaveformSpec(
    figure_id="Figure B45",
    official_title="Generalized Diagram of Direct Drive Friction Welding",
    short_title="Direct Drive Friction Welding Diagram",
    pages=[(161, 149)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    time_axis="TIME",
    traces=[
        TraceVariableSpec(
            name="ROTATIONAL SPEED",
            physical_quantity="Angular Velocity",
            unit="RPM",
            description="Continuous motor-driven rotation until braking deceleration.",
        ),
        TraceVariableSpec(
            name="AXIAL FORCE",
            physical_quantity="Force",
            unit="Newtons / Pounds-force",
            description="Two-stage force profile: friction welding force followed by forge force.",
        ),
        TraceVariableSpec(
            name="UPSET",
            physical_quantity="Length / Displacement",
            unit="Millimeters / Inches",
            description="Two-stage displacement: friction upset distance followed by forge upset distance.",
        ),
    ],
    intervals=[
        TemporalIntervalSpec(
            name="FRICTION TIME",
            order=1,
            description="The duration of relative motion under friction welding force.",
            clause4_term="friction welding",
        ),
        TemporalIntervalSpec(
            name="FORGE TIME",
            order=2,
            description="The time interval during which forge force is applied after rotation stops.",
            clause4_term="direct drive friction welding",
        ),
    ],
    parameters=[
        WaveformParameterSpec(
            name="FRICTION SPEED",
            associated_trace="ROTATIONAL SPEED",
            associated_interval="FRICTION TIME",
            description="The constant relative velocity during friction heating.",
        ),
        WaveformParameterSpec(
            name="FRICTION WELDING FORCE",
            associated_trace="AXIAL FORCE",
            associated_interval="FRICTION TIME",
            description="The compressive force applied during rotational heating.",
        ),
        WaveformParameterSpec(
            name="FORGE FORCE",
            associated_trace="AXIAL FORCE",
            associated_interval="FORGE TIME",
            description="Increased compressive force applied at or near cessation of rotation.",
        ),
        WaveformParameterSpec(
            name="FRICTION UPSET DISTANCE",
            associated_trace="UPSET",
            associated_interval="FRICTION TIME",
            description="Axial shortening during friction time.",
        ),
        WaveformParameterSpec(
            name="FORGE UPSET DISTANCE",
            associated_trace="UPSET",
            associated_interval="FORGE TIME",
            description="Additional axial shortening during forge time.",
        ),
        WaveformParameterSpec(
            name="TOTAL UPSET DISTANCE",
            associated_trace="UPSET",
            description="Total axial reduction from initial contact through forge completion.",
        ),
    ],
    compound_intervals=[
        {
            "name": "TOTAL WELDING TIME",
            "description": "Friction time plus forge time.",
            "clause4_term": "welding cycle",
        }
    ],
    notes=[
        "Direct drive friction welding uses continuous mechanical drive from a motor until disengaged and braked.",
    ],
    source_anomalies=[],
    clause4_terms=[
        "direct drive friction welding",
        "friction speed",
        "friction upset distance",
        "friction welding",
        "friction welding force",
        "upset distance",
    ],
)


# ---------------------------------------------------------------------------
# Figure B51: Electro-Mechanical Synchronization in a Typical Flash Welding Cycle
# ---------------------------------------------------------------------------
FIGURE_B51_SPEC = CycleWaveformSpec(
    figure_id="Figure B51",
    official_title="Electro-Mechanical Synchronization in a Typical Flash Welding Cycle",
    short_title="Flash Welding Synchronization Cycle",
    pages=[(166, 154)],
    crop_box=(0.05, 0.05, 0.95, 0.95),
    time_axis="TIME",
    traces=[
        TraceVariableSpec(
            name="PLATEN POSITION",
            physical_quantity="Displacement",
            unit="Millimeters / Inches",
            description="Movable platen advance during flashing and rapid upset.",
        ),
        TraceVariableSpec(
            name="PLATEN VELOCITY",
            physical_quantity="Velocity",
            unit="Millimeters/sec",
            description="Platen advance speed (parabolic/exponential acceleration during flashing).",
        ),
        TraceVariableSpec(
            name="FLASHING VOLTAGE",
            physical_quantity="Electric Potential",
            unit="Volts",
            description="Secondary voltage maintained across flashing gap.",
        ),
        TraceVariableSpec(
            name="UPSET FORCE",
            physical_quantity="Force",
            unit="Newtons / Pounds-force",
            description="High forge force applied to expel molten metal and produce coalescence.",
        ),
    ],
    intervals=[
        TemporalIntervalSpec(
            name="FLASH TIME",
            order=1,
            description="Period of the flash welding cycle during which flashing action occurs.",
            clause4_term="flash time",
        ),
        TemporalIntervalSpec(
            name="UPSET TIME",
            order=2,
            description="Period during which upsetting force is applied to produce coalescence and extrude molten film.",
            clause4_term="upset welding",
        ),
        TemporalIntervalSpec(
            name="HOLD TIME",
            order=3,
            description="The duration of force application after flashing and upset current ends.",
            clause4_term="hold time",
        ),
    ],
    parameters=[
        WaveformParameterSpec(
            name="FLASHING CURRENT",
            associated_trace="FLASHING VOLTAGE",
            associated_interval="FLASH TIME",
            description="Current passing through flashing bridges at faying surfaces.",
        ),
        WaveformParameterSpec(
            name="UPSET CURRENT",
            associated_trace="FLASHING VOLTAGE",
            associated_interval="UPSET TIME",
            description="High current surge applied during initiation of upsetting.",
        ),
    ],
    compound_intervals=[
        {
            "name": "TOTAL CYCLE TIME",
            "description": "Total elapsed time from platen advance through hold time.",
            "clause4_term": "welding cycle",
        }
    ],
    notes=[
        "Source credit on page 154: Reproduced from AWS C1.1M/C1.1:2019, Recommended Practices for Resistance Welding, Figure 31.",
    ],
    source_anomalies=[
        {
            "anomaly_id": "ANOMALY-B51-TITLE-ARTICLE",
            "description": "List of Figures (PDF index 11) writes 'in Typical Flash Welding Cycle' while page 154 caption writes 'in a Typical Flash Welding Cycle'.",
            "resolution": "Verified with flexible article matching in verify_figure_title_in_list_of_figures.",
        }
    ],
    clause4_terms=[
        "flash time",
        "hold time",
        "welding current",
    ],
)


# Master mapping of all Archetype 4 specifications
ARCHETYPE4_SPECS: Dict[str, CycleWaveformSpec] = {
    "Figure B44": FIGURE_B44_SPEC,
    "Figure B45": FIGURE_B45_SPEC,
    "Figure B49": FIGURE_B49_SPEC,
    "Figure B50": FIGURE_B50_SPEC,
    "Figure B51": FIGURE_B51_SPEC,
    "Figure B53": FIGURE_B53_SPEC,
    "Figure B54": FIGURE_B54_SPEC,
}
