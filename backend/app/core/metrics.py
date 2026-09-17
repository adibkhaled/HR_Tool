from __future__ import annotations

from collections import defaultdict
from threading import Lock


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self.counters: dict[str, float] = defaultdict(float)
        self.gauges: dict[str, float] = defaultdict(float)
        self.histograms: dict[str, list[float]] = defaultdict(list)

    def increment(self, name: str, value: float = 1) -> None:
        with self._lock:
            self.counters[name] += value

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self.gauges[name] = value

    def observe(self, name: str, value: float) -> None:
        with self._lock:
            self.histograms[name].append(value)

    def render(self) -> str:
        lines: list[str] = []
        with self._lock:
            for name, value in sorted(self.counters.items()):
                lines.extend([f"# TYPE {name} counter", f"{name} {value:g}"])
            for name, value in sorted(self.gauges.items()):
                lines.extend([f"# TYPE {name} gauge", f"{name} {value:g}"])
            for name, values in sorted(self.histograms.items()):
                if not values:
                    continue
                lines.extend([
                    f"# TYPE {name} histogram",
                    f"{name}_count {len(values)}",
                    f"{name}_sum {sum(values):g}",
                ])
        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        with self._lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()


metrics_registry = Metrics()
