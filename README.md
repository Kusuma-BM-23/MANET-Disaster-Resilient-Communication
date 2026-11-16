# MANET Version 4.0 — controlled research simulation

## Important scope
This is a more physically motivated educational simulator, not a validated field/network simulator. It includes a log-distance-inspired received-signal proxy with shadowing, obstacle attenuation, probabilistic packet errors, a CSMA/CA-like contention penalty, mobility, per-transmission energy accounting, node/link failures, priority SOS traffic and route recovery. Parameters are explicit and should be calibrated against measurements before making real-world claims.

## Install (Windows, Python 3.12)
```powershell
py -3.12 -m venv .venv_v4
.venv_v4\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
Or use your existing `.venv312`: activate it, then `python -m pip install -r requirements.txt`.

## Run
```powershell
python main.py --experiment
```
Default: 10 seeds, 3 disaster severities, 3 routing methods, 1800 simulation steps: 90 runs.
Mobility is fixed at 1.0 across severity levels so disaster severity is not confounded with mobility.
For a quick test:
```powershell
python main.py --experiment --seeds 2 --steps 300
```
For a different fixed mobility:
```powershell
python main.py --experiment --mobility 0.7
```

## Outputs in results_v4
- v4_raw_results.csv — one row per run
- v4_summary.csv — mean results per severity and protocol
- v4_pdr.png
- v4_sos.png
- v4_delay.png
- v4_throughput.png
- v4_energy.png

## Academic caveats
AODV-like and DSR-like are simplified route-selection abstractions, not RFC-conformant protocol implementations. The radio model is a simplified log-distance-inspired probability model; MAC contention is an approximation, not full IEEE 802.11 DCF. Units are simulation seconds/steps and Joules based on illustrative per-hop costs. Do not present results as measured real-world network performance. For rigorous protocol-level validation, implement the scenarios in ns-3 or OMNeT++ with a documented propagation/MAC model.
