# Project Report — Version 3.0

## Title
Disaster-Resilient Emergency Communication Using Mobile Ad Hoc Networks (MANET)

## Abstract
This project implements an educational simulation of a 50-node mobile ad hoc network for emergency communication in disaster-affected areas. The network contains rescue, ambulance, police, fire and emergency command-centre nodes. Version 3.0 introduces hazard regions that attenuate wireless links, two candidate command-centre destinations, SOS route selection, priority message handling, route rediscovery, and a multi-scenario experiment mode. A live Pygame dashboard visualizes topology, moving packets, node energy, failures, SOS delivery and routing statistics.

## Objectives
1. Simulate a 50-node infrastructure-independent wireless network.
2. Model node mobility, disaster-related node failures and damaged links.
3. Give SOS messages priority over routine packets.
4. Select an available command-centre destination and recover routes after link failure.
5. Compare AODV-like, DSR-like and adaptive routing.
6. Evaluate routing under Low, Medium and High disaster severity with multiple random seeds.

## Architecture
The application contains node mobility, wireless connectivity, disaster attenuation, routing, packet queue, failure and recovery, metrics, experiment runner and Pygame visualization modules. Nodes have role, position, velocity, energy and congestion attributes. Two control-centre nodes are used as possible emergency destinations.

## Routing methods
- AODV-like: on-demand shortest-hop route discovery.
- DSR-like: source-route caching while cached hops remain valid.
- Adaptive: weighted route cost based on residual energy, link quality, congestion and relative mobility.

## SOS handling
A field node is selected only if at least one command centre is reachable. The SOS packet is inserted at the front of the queue. When a route or link fails, the simulator attempts route rediscovery up to a bounded number of retries. A successful SOS route is highlighted in yellow in the visualization. A disconnected network cannot guarantee delivery; failed attempts must be reported as failures.

## Simulation configuration
| Parameter | Value |
|---|---:|
| Nodes | 50 |
| Rescue / Ambulance / Police / Fire / Control | 25 / 10 / 8 / 5 / 2 |
| Nominal radio range | 205 abstract coordinate units |
| Initial node energy | 100 units |
| Default benchmark duration | 900 steps |
| Packet payload | 512 bytes |
| Disaster severity | Low / Medium / High |
| Experiment random seeds | 11, 23, 37 |

## Metrics
PDR = delivered packets / generated packets × 100. Average delay = accumulated delivery delay / delivered packets. Throughput = delivered payload bits / simulation steps. Additional metrics include active nodes, residual energy, route repairs, SOS delivery and SOS reroutes.

## Execution
Install dependencies with `python -m pip install -r requirements.txt`.
Run `python main.py --visualize` for the live dashboard.
Run `python main.py` for the protocol comparison.
Run `python main.py --experiment` for the multi-seed severity experiments.

## Results
Use the measured `results/protocol_comparison.csv`, `results/scenario_experiments.csv` and `results/scenario_mean_pdr.csv`. Include the generated charts. Report averages across seeds and avoid claiming one routing method is superior unless supported by the measurements.

## Limitations
This is a custom educational model, not a standards-compliant implementation of AODV or DSR. Hazard zones are simplified rectangles that reduce link quality; the simulator does not implement full RF propagation, fading, shadowing, MAC contention or calibrated physical throughput. Simulation coordinates and steps are abstract.

## Future work
Validate protocols in NS-3 or OMNeT++; add map/GIS-based obstacles, realistic channel and MAC models, controlled mobility traces, retransmission policies, statistical confidence intervals and larger node populations.
