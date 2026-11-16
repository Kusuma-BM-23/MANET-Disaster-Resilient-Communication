# Version 4.0 methodology addendum

Version 4.0 separates disaster severity from mobility. Each severity is tested with the same mobility factor, the same scheduled emergency-alert times, the same set of random seeds, and the same packet generation schedule. The experiment is repeated for AODV-like, DSR-like and Adaptive routing.

The model adds a log-distance-inspired received-signal proxy, random shadowing, obstacle attenuation, probabilistic packet errors, a simplified contention penalty, per-hop transmit/receive energy accounting, and scheduled SOS traffic. Results include overall PDR, SOS delivery success, mean delay, throughput, energy consumption, active nodes and route repairs.

The radio and MAC layers remain approximations. The routing methods are educational abstractions rather than complete standards implementations. Use ns-3/OMNeT++ for protocol conformance and calibrated radio studies.
