import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { I18nProvider } from "../../shared/i18n/I18nProvider";
import type { ChannelStatus } from "../push/pushChannel";
import { PhaseHeader } from "./PhaseHeader";
import { UNKNOWN_PHASE, type PhaseView } from "./phaseView";

function renderHeader(
  phase: PhaseView,
  channel: ChannelStatus = "open",
  telemetryHz = 25,
) {
  render(
    <I18nProvider>
      <PhaseHeader phase={phase} channel={channel} telemetryHz={telemetryHz} />
    </I18nProvider>,
  );
}

/** The value shown under a label of the header. */
function valueOf(label: string): string | null | undefined {
  return screen.getByText(label).nextElementSibling?.textContent;
}

describe("PhaseHeader", () => {
  it("shows the previous, current and expected next phase and the time in phase", () => {
    renderHeader({
      previous: "BOOT",
      current: "SAFE_HOLD",
      expectedNext: "S0_IDLE",
      sinceS: 12.34,
    });

    expect(valueOf("Pha trước")).toBe("Khởi động BOOT");
    expect(valueOf("Pha hiện tại")).toBe("Chờ an toàn SAFE_HOLD");
    expect(valueOf("Pha kế tiếp dự kiến")).toBe("Nghỉ S0_IDLE");
    expect(valueOf("Thời gian ở pha")).toBe("12,3 s");
  });

  it("shows — for every value the telemetry did not give", () => {
    renderHeader(UNKNOWN_PHASE);

    expect(
      [
        "Pha trước",
        "Pha hiện tại",
        "Pha kế tiếp dự kiến",
        "Thời gian ở pha",
      ].map(valueOf),
    ).toEqual(["—", "—", "—", "—"]);
  });

  it.each<[ChannelStatus, number, string]>([
    ["open", 25, "Telemetry 25 Hz"],
    ["open", 0, "Telemetry 0 Hz"],
    ["connecting", 0, "Đang kết nối"],
    ["closed", 25, "Mất kết nối"],
  ])(
    "shows the telemetry rate only while connected: %s at %d Hz",
    (channel, hz, text) => {
      renderHeader(UNKNOWN_PHASE, channel, hz);

      expect(screen.queryByText(text)).not.toBeNull();
    },
  );
});
