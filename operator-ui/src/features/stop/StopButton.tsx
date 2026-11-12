import { useI18n } from "../../shared/i18n/I18nProvider";
import type { CommandStatus, CommandView } from "./commandLog";

interface StopButtonProps {
  command: CommandView | null;
  onStop: () => Promise<void>;
}

const STATUS_KEY = {
  pending: "hmi.command_state.pending",
  accepted: "hmi.command_state.accepted",
  rejected: "hmi.command_state.rejected",
  "timed-out": "hmi.command_state.timed_out",
  completed: "hmi.command_state.completed",
  unknown: "hmi.command_state.unknown",
} satisfies Record<CommandStatus, string>;

/**
 * Sends Stop at once, without a confirmation, and is never disabled (REQ-HMI-019).
 * A software stop, not the hardware emergency stop (ADR 0005).
 */
export function StopButton({ command, onStop }: StopButtonProps) {
  const { t } = useI18n();
  const label = t("hmi.stop.label");
  return (
    <div className="stop">
      <button
        type="button"
        className="stop-button"
        onClick={() => {
          void onStop();
        }}
      >
        {label}
      </button>
      {command && (
        <p className="command-progress">
          {t("hmi.command.progress", {
            command: label,
            state: t(STATUS_KEY[command.status]),
          })}
        </p>
      )}
    </div>
  );
}
