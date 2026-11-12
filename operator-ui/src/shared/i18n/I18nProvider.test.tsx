import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "./I18nProvider";
import { LocaleSwitch } from "./LocaleSwitch";
import { translate } from "./translate";

afterEach(() => {
  localStorage.clear();
});

function renderLocaleSwitch() {
  return render(
    <I18nProvider>
      <LocaleSwitch />
    </I18nProvider>,
  );
}

describe("I18nProvider", () => {
  it("shows Vietnamese until a language is chosen", () => {
    renderLocaleSwitch();

    expect(screen.getByLabelText<HTMLSelectElement>("Ngôn ngữ").value).toBe(
      "vi",
    );
    expect(document.documentElement.lang).toBe("vi");
    expect(document.title).toBe("Tay máy sạc xe điện");
  });

  it("switches to English at run time and remembers it in the browser", () => {
    const { unmount } = renderLocaleSwitch();

    fireEvent.change(screen.getByLabelText("Ngôn ngữ"), {
      target: { value: "en" },
    });

    expect(screen.getByLabelText<HTMLSelectElement>("Language").value).toBe(
      "en",
    );
    expect(document.documentElement.lang).toBe("en");
    unmount();
    renderLocaleSwitch();
    expect(screen.getByLabelText<HTMLSelectElement>("Language").value).toBe(
      "en",
    );
  });
});

describe("translate", () => {
  it("fills the parameters of a message", () => {
    expect(translate("en", "hmi.telemetry.rate", { rate: 25 })).toBe(
      "Telemetry 25 Hz",
    );
  });

  it("shows a missing key as the key itself and warns the developer", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);

    expect(translate("vi", "hmi.test.absent_key")).toBe("hmi.test.absent_key");
    expect(warn).toHaveBeenCalledWith(
      expect.stringContaining("hmi.test.absent_key"),
    );
  });
});
