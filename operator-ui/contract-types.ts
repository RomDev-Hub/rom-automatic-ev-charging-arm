// Writes the TypeScript types of the HMI contracts (ADR 0006) to src/shared/contracts/; with --check, fails instead when a committed file differs.
import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import openapiTS, {
  astToString,
  type OpenAPI3,
  type OpenAPITSOptions,
  type SchemaObject,
} from "openapi-typescript";
import { format, resolveConfig } from "prettier";
import { parse } from "yaml";

const CONTRACTS = new URL("../contracts/", import.meta.url);
const OUTPUT = new URL("src/shared/contracts/", import.meta.url);
const OPTIONS: OpenAPITSOptions = { emptyObjectsUnknown: true, silent: true };
const SCHEMA_REF = "#/components/schemas/";
const MESSAGE_REF = "#/components/messages/";

interface Reference {
  $ref: string;
}

interface AsyncApiDocument {
  info: OpenAPI3["info"];
  channels: Record<
    string,
    { address: string; messages: Record<string, Reference> }
  >;
  components: {
    messages: Record<string, { payload?: unknown }>;
    schemas: Record<string, SchemaObject>;
  };
}

async function restTypes(): Promise<string> {
  const text = await readFile(new URL("openapi.json", CONTRACTS), "utf8");
  return astToString(await openapiTS(JSON.parse(text) as OpenAPI3, OPTIONS));
}

// The AsyncAPI payloads are JSON Schema: inside an OpenAPI 3.1 shell their references to #/components/schemas/ resolve unchanged.
async function pushTypes(): Promise<string> {
  const text = await readFile(new URL("asyncapi.yaml", CONTRACTS), "utf8");
  const document = parse(text) as AsyncApiDocument;
  const shell: OpenAPI3 = {
    openapi: "3.1.0",
    info: document.info,
    paths: {},
    components: { schemas: document.components.schemas },
  };
  return astToString(await openapiTS(shell, OPTIONS)) + channelTypes(document);
}

function channelTypes(document: AsyncApiDocument): string {
  const channels = Object.entries(document.channels).map(([name, channel]) => {
    const payloads = Object.values(channel.messages).map(
      (message) =>
        `components["schemas"]["${payloadSchema(document, message)}"]`,
    );
    return `${name}: { address: ${JSON.stringify(channel.address)}; message: ${payloads.join(" | ")} };`;
  });
  return `export interface channels {\n${channels.join("\n")}\n}\n`;
}

function payloadSchema(document: AsyncApiDocument, message: Reference): string {
  const name = message.$ref.replace(MESSAGE_REF, "");
  const payload = document.components.messages[name]?.payload;
  if (!isReference(payload) || !payload.$ref.startsWith(SCHEMA_REF)) {
    throw new Error(
      `message ${name}: the payload must be a $ref to ${SCHEMA_REF}`,
    );
  }
  return payload.$ref.replace(SCHEMA_REF, "");
}

function isReference(value: unknown): value is Reference {
  return (
    typeof value === "object" &&
    value !== null &&
    "$ref" in value &&
    typeof value.$ref === "string"
  );
}

async function render(
  file: string,
  source: string,
  types: string,
): Promise<string> {
  const options = await resolveConfig(fileURLToPath(new URL(file, OUTPUT)), {
    editorconfig: true,
  });
  const header = `// Generated from contracts/${source} by contract-types.ts; do not edit.\n`;
  return format(header + types, { ...options, parser: "typescript" });
}

const files = new Map([
  ["openapi.ts", await render("openapi.ts", "openapi.json", await restTypes())],
  [
    "asyncapi.ts",
    await render("asyncapi.ts", "asyncapi.yaml", await pushTypes()),
  ],
]);

if (process.argv.includes("--check")) {
  const stale: string[] = [];
  for (const [file, contents] of files) {
    const committed = await readFile(new URL(file, OUTPUT), "utf8").catch(
      () => "",
    );
    if (committed !== contents) stale.push(file);
  }
  if (stale.length > 0) {
    console.error(
      `stale contract types in src/shared/contracts/: ${stale.join(", ")}; run pnpm --filter operator-ui run contracts`,
    );
    process.exitCode = 1;
  }
} else {
  for (const [file, contents] of files) {
    await writeFile(new URL(file, OUTPUT), contents);
  }
}
