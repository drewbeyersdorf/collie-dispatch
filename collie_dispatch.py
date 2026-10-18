#!/usr/bin/env python3
"""collie-dispatch: the pen is the queue.

Tasks arrive as a flock. The collie holds them in a calm bunch, then sheds
one at a time to the right worker. No task is grabbed twice; no task
starves at the back of the pen; the pen is visible, not a hidden list.

Demo: python3 collie_dispatch.py demo
"""
import json, time, heapq, itertools
from dataclasses import dataclass, field

@dataclass(order=True)
class Task:
    priority: int
    born: float
    id: str = field(compare=False)
    kind: str = field(compare=False)
    payload: dict = field(compare=False)
    claimed_by: str | None = field(default=None, compare=False)
    attempts: int = field(default=0, compare=False)

class Pen:
    """The visible holding pen. Starvation guard: oldest eligible task gets
    a priority boost every `sigh_seconds` it waits unclaimed."""
    def __init__(self, sigh_seconds: float = 30.0):
        self._heap: list[Task] = []
        self._counter = itertools.count()
        self._claimed: dict[str, Task] = {}
        self.sigh_seconds = sigh_seconds

    def gather(self, task_id: str, kind: str, payload: dict, priority: int = 5):
        heapq.heappush(self._heap, Task(priority, time.time() + next(self._counter) * 1e-6,
                                        task_id, kind, payload))

    def shed(self, worker: str, kinds: set[str] | None = None) -> Task | None:
        """Peel one task cleanly from the bunch for this worker."""
        now = time.time()
        skipped: list[Task] = []
        chosen = None
        while self._heap:
            t = heapq.heappop(self._heap)
            waited = now - t.born
            if self.sigh_seconds > 0 and waited > self.sigh_seconds:
                t.priority -= int(waited // self.sigh_seconds)  # starvation boost
            if kinds is None or t.kind in kinds:
                if t.id in self._claimed:
                    continue  # already shed; skip the ghost
                chosen = t
                break
            skipped.append(t)
        for t in skipped:
            heapq.heappush(self._heap, t)
        if chosen:
            chosen.claimed_by = worker
            chosen.attempts += 1
            self._claimed[chosen.id] = chosen
        return chosen

    def settle(self, task_id: str, ok: bool, note: str = "") -> dict:
        """Worker reports back; the mark goes on the gate for all to read."""
        t = self._claimed.pop(task_id, None)
        if t is None:
            return {"id": task_id, "settled": False, "note": "unknown or double-settle"}
        receipt = {"id": t.id, "kind": t.kind, "worker": t.claimed_by,
                   "ok": ok, "attempts": t.attempts, "note": note,
                   "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        print(("PASS " if ok else "FAIL ") + json.dumps(receipt))
        return receipt

    def visible(self) -> list[str]:
        return sorted(f"{t.kind}:{t.id}(p{t.priority})" for t in self._heap)

def demo():
    pen = Pen(sigh_seconds=0.000001)  # near-instant starvation boost for the demo
    pen.gather("build-57", "build", {"rounds": 57}, priority=5)
    pen.gather("post-menagerie", "post", {"channel": "draft"}, priority=5)
    pen.gather("watch-board", "watch", {}, priority=9)  # low priority, would starve
    skid = pen.shed("skid", kinds={"build"})
    cali = pen.shed("caliper", kinds={"post"})
    hark = pen.shed("hark", kinds={"watch"})  # boosted out of starvation
    for t, ok in ((skid, True), (cali, True), (hark, False)):
        if t: pen.settle(t.id, ok, "demo")
    ghost = pen.settle("build-57", True, "double-settle attempt")
    assert ghost["settled"] is False
    print("pen visible:", pen.visible())

if __name__ == "__main__":
    demo()
