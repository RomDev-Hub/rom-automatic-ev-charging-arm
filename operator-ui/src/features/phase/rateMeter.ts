const WINDOW_MS = 1_000;

/** Telemetry receive rate in Hz: the snapshots received within the last second (REQ-HMI-015). */
export class RateMeter {
  #arrivalsMs: number[] = [];

  record(nowMs: number): void {
    this.#arrivalsMs.push(nowMs);
  }

  rateHz(nowMs: number): number {
    const kept = this.#arrivalsMs.findIndex(
      (arrivalMs) => arrivalMs > nowMs - WINDOW_MS,
    );
    this.#arrivalsMs = kept === -1 ? [] : this.#arrivalsMs.slice(kept);
    return this.#arrivalsMs.length;
  }

  clear(): void {
    this.#arrivalsMs = [];
  }
}
