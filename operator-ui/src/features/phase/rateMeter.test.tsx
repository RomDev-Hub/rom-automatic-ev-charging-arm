import { describe, expect, it } from "vitest";
import { RateMeter } from "./rateMeter";

describe("RateMeter", () => {
  it("counts the snapshots of the last second", () => {
    const meter = new RateMeter();
    for (let arrivalMs = 0; arrivalMs < 2_000; arrivalMs += 40) {
      meter.record(arrivalMs);
    }

    expect(meter.rateHz(1_960)).toBe(25);
  });

  it("falls to 0 once snapshots stop coming", () => {
    const meter = new RateMeter();
    meter.record(0);
    meter.record(40);

    expect(meter.rateHz(500)).toBe(2);
    expect(meter.rateHz(1_100)).toBe(0);
  });
});
