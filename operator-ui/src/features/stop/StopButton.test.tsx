import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../../shared/i18n/I18nProvider";
import type { CommandView } from "./commandLog";
import { StopButton } from "./StopButton";

function renderStop(command: CommandView | null, onStop = vi.fn()) {
  render(
    <I18nProvider>
      <StopButton command={command} onStop={onStop} />
    </I18nProvider>,
  );
  return onStop;
}

afterEach(() => {
  localStorage.clear();
});

describe("StopButton", () => {
  it("is labelled Dừng in Vietnamese and stays enabled", () => {
    renderStop(null);

    expect(screen.getByRole("button", { name: "Dừng" })).toHaveProperty(
      "disabled",
      false,
    );
  });

  it("is labelled Stop in English", () => {
    localStorage.setItem("ev-arm.locale", "en");

    renderStop(null);

    expect(screen.getByRole("button").textContent).toBe("Stop");
  });

  it("sends the Stop command on the first click, without confirmation", () => {
    const onStop = renderStop(
      null,
      vi.fn(() => Promise.resolve()),
    );

    fireEvent.click(screen.getByRole("button", { name: "Dừng" }));

    expect(onStop).toHaveBeenCalledTimes(1);
  });

  it.each([
    ["accepted", "Lệnh Dừng: đã nhận"],
    ["timed-out", "Lệnh Dừng: quá hạn"],
    ["unknown", "Lệnh Dừng: chưa rõ"],
  ] as const)("shows the latest command as %s", (status, text) => {
    renderStop({ key: 1, commandId: "c-1", status });

    expect(screen.queryByText(text)).not.toBeNull();
  });
});
