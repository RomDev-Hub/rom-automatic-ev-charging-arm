import { useEffect } from "react";
import type { Notice } from "./api/rest";
import { useI18n } from "./i18n/I18nProvider";

export interface ToastView {
  id: number;
  notice: Notice;
}

// REQ-HMI-008: a command result shows for 2.6 s.
const SHOWN_MS = 2_600;

/** Short message built from a code and its parameters, hidden after a while; the region stays so screen readers hear each message. */
export function Toast({
  toast,
  onDismiss,
}: {
  toast: ToastView | null;
  onDismiss: (id: number) => void;
}) {
  const { t } = useI18n();

  useEffect(() => {
    if (toast === null) return;
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, SHOWN_MS);
    return () => {
      clearTimeout(timer);
    };
  }, [toast, onDismiss]);

  return (
    <div className="toast-region" role="status">
      {toast && (
        <p className="toast">{t(toast.notice.code, toast.notice.params)}</p>
      )}
    </div>
  );
}
