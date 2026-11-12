// Generated from contracts/openapi.json by contract-types.ts; do not edit.
export interface paths {
  "/api/health": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Read Health
     * @description Answer 200 while every health check passes, else 503 naming the failing.
     *
     *     The checks: the supervision loop ticked within the last second, the arm port
     *     is connected with fresh data and no latched fault, and the kinematics library
     *     is loaded. No session is needed and no operating data is returned
     *     (REQ-GW-023).
     */
    get: operations["read_health_api_health_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/session": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Read Session
     * @description The account and roles of the current session.
     */
    get: operations["read_session_api_session_get"];
    put?: never;
    /**
     * Open Session
     * @description Log in, and receive the session cookie.
     *
     *     The cookie is Secure, HttpOnly and SameSite=Strict, with a new identifier
     *     each time (REQ-AUTH-004). Credentials travel in the body, never in the URL
     *     (REQ-AUTH-005).
     */
    post: operations["open_session_api_session_post"];
    /**
     * Close Session
     * @description Log out: the session ends on the server and the cookie is cleared.
     */
    delete: operations["close_session_api_session_delete"];
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/commands/stop": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Stop
     * @description Stop: the arm stops at once, then the machine enters SAFE_STOP.
     *
     *     An operational stop through software, not a safety function: the safety
     *     functions are hardware (ADR 0005, REQ-MIS-066). Only a restart leaves
     *     SAFE_STOP until the resume command exists.
     */
    post: operations["stop_api_commands_stop_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/telemetry": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Read Telemetry
     * @description The latest telemetry snapshot, as pushed on /api/ws (REQ-GW-019).
     */
    get: operations["read_telemetry_api_telemetry_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
}
export type webhooks = Record<string, never>;
export interface components {
  schemas: {
    /**
     * BlockUnavailable
     * @description A block that could not be built (REQ-GW-017).
     */
    BlockUnavailable: {
      /**
       * Unavailable
       * @default true
       * @constant
       */
      unavailable: true;
      /**
       * Code
       * @default err.telemetry.block_unavailable
       */
      code: string;
    };
    /**
     * CommandResult
     * @description Result of a command the core carried out (REQ-GW-013).
     */
    CommandResult: {
      /**
       * Command Id
       * @description Tags the command's lifecycle messages on /api/ws (REQ-GW-007).
       */
      command_id: string;
      /** Command */
      command: string;
      /** Code */
      code: string;
      /** Params */
      params: {
        [key: string]: unknown;
      };
      /** @description Mission phase once the command was handled. */
      phase: components["schemas"]["Phase"];
    };
    /** Credentials */
    Credentials: {
      /** Username */
      username: string;
      /** Password */
      password: string;
    };
    /**
     * HealthReport
     * @description Every health check passes.
     */
    HealthReport: {
      /**
       * Status
       * @constant
       */
      status: "ok";
    };
    /**
     * Phase
     * @description Phases of the mission state machine, named as in contracts/asyncapi.yaml.
     * @enum {string}
     */
    Phase: "BOOT" | "SAFE_HOLD" | "S0_IDLE" | "SAFE_STOP";
    /**
     * PhaseBlock
     * @description Current phase and the latest phase change (REQ-MIS-004).
     */
    PhaseBlock: {
      phase: components["schemas"]["Phase"];
      previous: components["schemas"]["Phase"];
      expected_next: components["schemas"]["Phase"] | null;
      /**
       * Since S
       * @description Time in the current phase (s), on the monotonic clock.
       */
      since_s: number;
      note: components["schemas"]["PhaseNote"];
    };
    /**
     * PhaseNote
     * @description Reason code and parameters of the latest phase change.
     */
    PhaseNote: {
      /** Code */
      code: string;
      /** Params */
      params: {
        [key: string]: unknown;
      };
    };
    /**
     * Role
     * @description Account roles of docs/requirements/gateway-config-data.md.
     * @enum {string}
     */
    Role: "operator" | "maintainer" | "admin";
    /**
     * SessionInfo
     * @description The account of the session, without any secret (REQ-AUTH-008).
     */
    SessionInfo: {
      /** Username */
      username: string;
      /** Roles */
      roles: components["schemas"]["Role"][];
    };
    /**
     * TelemetryData
     * @description One telemetry snapshot (REQ-GW-016), alike on /api/ws and over REST.
     */
    TelemetryData: {
      /**
       * Data Origin
       * @enum {string}
       */
      data_origin: "measured" | "simulated";
      /** Phase */
      phase:
        | components["schemas"]["PhaseBlock"]
        | components["schemas"]["BlockUnavailable"];
      safe_hold: components["schemas"]["BlockUnavailable"];
      supervision: components["schemas"]["BlockUnavailable"];
      session: components["schemas"]["BlockUnavailable"];
      lot: components["schemas"]["BlockUnavailable"];
      motion: components["schemas"]["BlockUnavailable"];
      devices: components["schemas"]["BlockUnavailable"];
      perception: components["schemas"]["BlockUnavailable"];
      sim_faults: components["schemas"]["BlockUnavailable"];
      health: components["schemas"]["BlockUnavailable"];
      build: components["schemas"]["BlockUnavailable"];
    };
    /**
     * ProblemCode
     * @description Catalogue codes the gateway answers with.
     * @enum {string}
     */
    ProblemCode:
      | "err.auth.required"
      | "err.auth.invalid_credentials"
      | "err.not_found"
      | "err.internal"
      | "err.not_ready"
      | "cmd.bad_params"
      | "cmd.unknown";
    /**
     * Problem
     * @description Problem details (RFC 9457) with the catalogue code and its parameters.
     */
    Problem: {
      /** Type */
      type: string;
      /** Status */
      status: number;
      /** Title */
      title: string;
      code: components["schemas"]["ProblemCode"];
      /** Params */
      params: {
        [key: string]: unknown;
      };
    };
  };
  responses: never;
  parameters: never;
  requestBodies: never;
  headers: never;
  pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
  read_health_api_health_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HealthReport"];
        };
      };
      /** @description `err.not_ready`: System not ready */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_session_api_session_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SessionInfo"];
        };
      };
      /** @description `err.auth.required`: Not signed in or the session has expired */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  open_session_api_session_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["Credentials"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SessionInfo"];
        };
      };
      /** @description `err.auth.invalid_credentials`: Incorrect username or password */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description `cmd.bad_params`: Command parameters missing, mistyped or out of range */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  close_session_api_session_delete: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description `err.auth.required`: Not signed in or the session has expired */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  stop_api_commands_stop_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CommandResult"];
        };
      };
      /** @description `err.auth.required`: Not signed in or the session has expired */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description `err.internal`: Internal system error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_telemetry_api_telemetry_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["TelemetryData"];
        };
      };
      /** @description `err.auth.required`: Not signed in or the session has expired */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description `err.not_ready`: System not ready */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
}
