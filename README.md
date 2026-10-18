# collie-dispatch
Dispatch as a gathering pen: tasks arrive as a flock, the collie holds them in a calm bunch, then sheds one at a time to the right worker.
- Animal behavior: gathering and shedding - bring the group together without scattering it, then peel off singles cleanly.
- Fleet mechanism: a claim queue with backpressure. No task is grabbed twice; no task starves at the back of the flock; the queue is visible as a pen, not a list.
Status: private staging. Part of the HERDR animal-harness series.
