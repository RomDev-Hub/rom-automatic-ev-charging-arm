// Generated from contracts/asyncapi.yaml by contract-types.ts; do not edit.
export type paths = Record<string, never>;
export type webhooks = Record<string, never>;
export interface components {
  schemas: {
    /** @description Envelope theo CloudEvents 1.0, chung cho mọi thông điệp của kênh. */
    Envelope: {
      /**
       * @description Phiên bản CloudEvents.
       * @constant
       */
      specversion: "1.0";
      /** @description Định danh của thông điệp, duy nhất trong phạm vi `source`. */
      id: string;
      /**
       * Format: uri-reference
       * @description `/core/` cộng ID phiên chạy của `core` (REQ-REC-013).
       */
      source: string;
      /** @description Loại thông điệp, tiền tố `io.github.romdev-hub.ev-arm.`. */
      type: string;
      /**
       * Format: date-time
       * @description Thời điểm xảy ra theo RFC 3339, giờ UTC của host.
       */
      time: string;
      /** @description Thứ tự của thông điệp trong phạm vi `source`, 20 chữ số thập phân, tăng 1 sau mỗi thông điệp. */
      sequence: string;
      data: Record<string, unknown>;
    };
    TelemetrySnapshot: components["schemas"]["Envelope"] & {
      /** @constant */
      type?: "io.github.romdev-hub.ev-arm.telemetry.snapshot";
      data?: components["schemas"]["TelemetryData"];
    };
    PhaseChanged: components["schemas"]["Envelope"] & {
      /** @constant */
      type?: "io.github.romdev-hub.ev-arm.phase.changed";
      data?: components["schemas"]["PhaseChangedData"];
    };
    MotionBlocked: components["schemas"]["Envelope"] & {
      /** @constant */
      type?: "io.github.romdev-hub.ev-arm.motion.blocked";
      data?: components["schemas"]["MotionBlockedData"];
    };
    FaultRaised: components["schemas"]["Envelope"] & {
      /** @constant */
      type?: "io.github.romdev-hub.ev-arm.fault.raised";
      data?: components["schemas"]["FaultRaisedData"];
    };
    SupervisionChanged: components["schemas"]["Envelope"] & {
      /** @constant */
      type?: "io.github.romdev-hub.ev-arm.supervision.changed";
      data?: components["schemas"]["SupervisionChangedData"];
    };
    CommandLifecycle: components["schemas"]["Envelope"] & {
      /** @constant */
      type?: "io.github.romdev-hub.ev-arm.command.lifecycle";
      data?: components["schemas"]["CommandLifecycleData"];
    };
    /** @description Mã ổn định; mã lỗi và cảnh báo lấy từ `contracts/schemas/error-codes.schema.json` (REQ-I18N-004). */
    Code: string;
    /** @description Tham số của mã, khoá viết snake_case; câu hiển thị thay tham số vào câu của mã trong locale (REQ-I18N-004). */
    Params: {
      [key: string]: unknown;
    };
    /**
     * @description Trạng thái của máy trạng thái mission (REQ-MIS-001).
     * @enum {string}
     */
    Phase:
      | "BOOT"
      | "S0_IDLE"
      | "S1_VEHICLE_APPROACHING"
      | "S2_VEHICLE_SETTLING"
      | "DRIVER_EGRESS"
      | "BAY_CLEAR"
      | "S3_IDENTIFYING"
      | "S4_SESSION_AUTHORIZING"
      | "S5_LID_REQUEST"
      | "S6_PRECHECK"
      | "S7_ARM_TRANSIT"
      | "S8_PORT_SEARCH"
      | "S9_PORT_REFINE"
      | "S10_ALIGN"
      | "S11_INSERT"
      | "S12_SEAT_VERIFY"
      | "S13_LOCK"
      | "S14_HANDSHAKE"
      | "S15_CHARGING"
      | "S16_STOPPING"
      | "S17_UNLOCK_WAIT"
      | "S18_EXTRACT"
      | "S19_RETRACT_STOW"
      | "S20_POST_CHARGE"
      | "S21_VEHICLE_DEPARTING"
      | "SAFE_HOLD"
      | "RETRY_SEARCH"
      | "RETRY_INSERT"
      | "ABORT_UNPLUG"
      | "ABORT_RETRACT"
      | "CONNECTOR_STUCK"
      | "SAFE_STOP"
      | "HUMAN_PRESENT_PAUSE"
      | "WEATHER_HOLD"
      | "CALIBRATION_BLOCKED"
      | "MAINTENANCE"
      | "SESSION_FAILED";
    /** @description Trạng thái kỳ vọng kế tiếp (REQ-MIS-005); `null` khi danh mục trạng thái của bản đang chạy chưa có trạng thái kế cho trạng thái hiện tại. */
    ExpectedNext: components["schemas"]["Phase"] | null;
    /**
     * @description Mức giám sát (REQ-MIS-073).
     * @enum {string}
     */
    SupervisionLevel: "OK" | "SLOW" | "HOLD" | "STOP" | "ESTOP";
    /**
     * @description Trạng thái trong vòng đời của một lệnh REST.
     * @enum {string}
     */
    CommandState:
      "pending" | "accepted" | "rejected" | "timed-out" | "completed";
    /** @description Mã lý do và tham số của lần chuyển pha gần nhất (REQ-MIS-004). */
    PhaseNote: {
      code: components["schemas"]["Code"];
      params: components["schemas"]["Params"];
    };
    PhaseChangedData: {
      previous: components["schemas"]["Phase"];
      phase: components["schemas"]["Phase"];
      code: components["schemas"]["Code"];
      params: components["schemas"]["Params"];
      expected_next: components["schemas"]["ExpectedNext"];
    };
    MotionBlockedData: {
      code: components["schemas"]["Code"];
      params: components["schemas"]["Params"];
      /**
       * @description Nguồn của lệnh bị chặn (REQ-MOT-015).
       * @enum {string}
       */
      origin?: "auto" | "jog" | "home";
    };
    FaultRaisedData: {
      code: components["schemas"]["Code"];
      params: components["schemas"]["Params"];
    };
    SupervisionChangedData: {
      level: components["schemas"]["SupervisionLevel"];
      previous: components["schemas"]["SupervisionLevel"];
      code?: components["schemas"]["Code"];
      params?: components["schemas"]["Params"];
    };
    CommandLifecycleData: {
      /** @description ID mà route REST trả khi nhận lệnh; dạng ID chưa chốt (REQ-GW-025, đề xuất). */
      command_id: string;
      /** @description Tên lệnh, ví dụ `start_session`. */
      command: string;
      state: components["schemas"]["CommandState"];
      code?: components["schemas"]["Code"];
      params?: components["schemas"]["Params"];
    };
    /** @description Khối telemetry không dựng được (REQ-GW-017). */
    BlockUnavailable: {
      /** @constant */
      unavailable: true;
      code: components["schemas"]["Code"];
      params?: components["schemas"]["Params"];
    };
    /** @description Khối telemetry mà nội dung chi tiết do requirement của vùng sở hữu quy định; schema chi tiết chưa viết. */
    OpenBlock: {
      [key: string]: unknown;
    };
    /** @description Các khối của telemetry (REQ-GW-016); khối nào không dựng được thì là `BlockUnavailable`. */
    TelemetryData: {
      /**
       * @description Số liệu đo từ thiết bị thật hay từ adapter mô phỏng.
       * @enum {string}
       */
      data_origin: "measured" | "simulated";
      phase:
        | components["schemas"]["PhaseBlock"]
        | components["schemas"]["BlockUnavailable"];
      safe_hold:
        | components["schemas"]["SafeHoldBlock"]
        | components["schemas"]["BlockUnavailable"];
      supervision:
        | components["schemas"]["SupervisionBlock"]
        | components["schemas"]["BlockUnavailable"];
      /** @description Phiên sạc của bay đang phục vụ (REQ-HAL-037). */
      session:
        | components["schemas"]["OpenBlock"]
        | components["schemas"]["BlockUnavailable"];
      /** @description Bãi, trạng thái từng bay, hàng đợi điều phối và danh mục xe (REQ-MIS-077, REQ-MIS-078). */
      lot:
        | components["schemas"]["OpenBlock"]
        | components["schemas"]["BlockUnavailable"];
      /** @description Chuyển động, động học và mô-men (REQ-MOT-011, REQ-MOT-012, REQ-ARM-026). */
      motion:
        | components["schemas"]["OpenBlock"]
        | components["schemas"]["BlockUnavailable"];
      /** @description Health và số đo của các port ArmPort, Rail, Io, Presence, Force và Evse (REQ-HAL-005, REQ-HAL-024). */
      devices:
        | components["schemas"]["OpenBlock"]
        | components["schemas"]["BlockUnavailable"];
      /** @description Camera và perception (REQ-PER-007, REQ-PER-048). */
      perception:
        | components["schemas"]["OpenBlock"]
        | components["schemas"]["BlockUnavailable"];
      sim_faults:
        | components["schemas"]["SimFaultsBlock"]
        | components["schemas"]["BlockUnavailable"];
      /** @description Tình trạng của cấu hình trạm, bản ghi MCAP và log (REQ-CFG-005). */
      health:
        | components["schemas"]["OpenBlock"]
        | components["schemas"]["BlockUnavailable"];
      build:
        | components["schemas"]["BuildBlock"]
        | components["schemas"]["BlockUnavailable"];
    };
    /** @description Pha hiện tại và lần chuyển pha gần nhất (REQ-MIS-004). */
    PhaseBlock: {
      phase: components["schemas"]["Phase"];
      previous: components["schemas"]["Phase"];
      expected_next: components["schemas"]["ExpectedNext"];
      /** @description Thời gian đã ở pha hiện tại (s), đo bằng đồng hồ monotonic. */
      since_s: number;
      note: components["schemas"]["PhaseNote"];
    };
    /** @description Trạng thái SAFE_HOLD, cùng kết quả đánh giá mà FSM dùng (REQ-MIS-016). */
    SafeHoldBlock: {
      active: boolean;
      /** @description Lý do giữ, ví dụ `boot` hay `fault` (REQ-MIS-010, REQ-MIS-013). */
      reason?: string | null;
      /** @description Mục `chk.*` đạt. */
      passed: components["schemas"]["Code"][];
      /** @description Mục `chk.*` trượt. */
      failed: components["schemas"]["Code"][];
      /** @description Đã có lệnh xác nhận của người hay chưa (REQ-MIS-020). */
      acknowledged: boolean;
      /** @description Cờ nghi đầu sạc trong cổng (REQ-MIS-014, REQ-MIS-023). */
      connector_in_inlet: boolean;
      /** @description Lý do của cờ, mã `safehold.*` lúc khởi động (REQ-MIS-014). */
      connector_reason?: components["schemas"]["Code"] | null;
    };
    /** @description Mức giám sát và khoảng hở (REQ-MIS-073, REQ-MOT-022). */
    SupervisionBlock: {
      level: components["schemas"]["SupervisionLevel"];
      /** @description Hệ số tốc độ của mức giám sát. */
      speed_factor: number;
      code?: components["schemas"]["Code"];
      params?: components["schemas"]["Params"];
      /** @description Khoảng cách tới người gần nhất (m); `null` khi không có số đo. */
      person_clearance_m?: number | null;
      /** @description Khoảng hở nhỏ nhất giữa tay máy cùng thân đầu sạc và vỏ bao xe (m); `null` khi không tính được. */
      body_clearance_m?: number | null;
    };
    /** @description Lỗi giả lập đang bật (REQ-SIM-016); luôn rỗng khi chạy với adapter thật. */
    SimFaultsBlock: {
      active: {
        /** @description Mã lỗi giả lập trong danh mục lỗi giả lập (REQ-SIM-016). */
        fault: string;
        /** @description Tên lỗi giả lập, ví dụ `CAMERA_DROPOUT`. */
        name: string;
        code: components["schemas"]["Code"];
        /** @description Thời gian còn lại của lỗi (s), theo đồng hồ mà FSM dùng. */
        remaining_s: number;
      }[];
    };
    /** @description Phiên bản đang chạy. */
    BuildBlock: {
      /** @description Phiên bản SemVer của bản đang chạy (ADR 0009). */
      version: string;
      /** @description Commit của bản đang chạy. */
      commit: string;
    };
  };
  responses: never;
  parameters: never;
  requestBodies: never;
  headers: never;
  pathItems: never;
}
export type $defs = Record<string, never>;
export type operations = Record<string, never>;
export interface channels {
  push: {
    address: "/api/ws";
    message:
      | components["schemas"]["TelemetrySnapshot"]
      | components["schemas"]["PhaseChanged"]
      | components["schemas"]["MotionBlocked"]
      | components["schemas"]["FaultRaised"]
      | components["schemas"]["SupervisionChanged"]
      | components["schemas"]["CommandLifecycle"];
  };
}
