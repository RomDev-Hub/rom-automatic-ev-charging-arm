import { MISSING } from "../../shared/format";
import { useI18n } from "../../shared/i18n/I18nProvider";
import type { ChannelStatus } from "../push/pushChannel";
import type { PhaseView } from "./phaseView";

interface PhaseHeaderProps {
  phase: PhaseView;
  channel: ChannelStatus;
  telemetryHz: number;
}

const CHANNEL_STATE = {
  connecting: "hmi.telemetry.connecting",
  closed: "hmi.telemetry.disconnected",
} as const;

/** Phases and telemetry rate at the top of every view (REQ-HMI-014, REQ-HMI-015). */
export function PhaseHeader({ phase, channel, telemetryHz }: PhaseHeaderProps) {
  const { locale, t } = useI18n();
  const { sinceS } = phase;
  const timeInPhase =
    sinceS !== null && Number.isFinite(sinceS)
      ? t("hmi.phase.seconds", {
          seconds: new Intl.NumberFormat(locale, {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1,
          }).format(sinceS),
        })
      : MISSING;

  return (
    <section className="phase-header">
      <dl className="phase-list">
        <PhaseItem label={t("hmi.phase.previous")} phase={phase.previous} />
        <PhaseItem label={t("hmi.phase.current")} phase={phase.current} />
        <PhaseItem
          label={t("hmi.phase.expected_next")}
          phase={phase.expectedNext}
        />
        <div className="phase-item">
          <dt>{t("hmi.phase.time_in_phase")}</dt>
          <dd>{timeInPhase}</dd>
        </div>
      </dl>
      <p className={`telemetry-status telemetry-status--${channel}`}>
        {channel === "open"
          ? t("hmi.telemetry.rate", { rate: telemetryHz })
          : t(CHANNEL_STATE[channel])}
      </p>
    </section>
  );
}

function PhaseItem({ label, phase }: { label: string; phase: string | null }) {
  const { t } = useI18n();
  return (
    <div className="phase-item">
      <dt>{label}</dt>
      <dd>
        {phase === null ? (
          MISSING
        ) : (
          <>
            {t(`phase.name.${phase.toLowerCase()}`)}{" "}
            <code className="phase-id">{phase}</code>
          </>
        )}
      </dd>
    </div>
  );
}
