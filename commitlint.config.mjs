// Luật kiểm thông điệp commit, chạy ở hook commit-msg và trên CI.
// Quy ước đầy đủ nằm ở mục "Quy ước commit" trong CONTRIBUTING.md; sửa bảng ở đây thì sửa bảng ở đó trong cùng một commit.

// Label của body commit, theo đúng thứ tự phải viết.
const LABELS = ["Why", "What", "How", "Rejected", "Test", "Impact"];

// Label bắt buộc theo scope khi type làm đổi hành vi; type khác (trừ revert) chỉ cần Why.
const LABELS_BY_SCOPE = {
  safety: ["Why", "How", "Rejected", "Test", "Impact"],
  motion: ["Why", "How", "Test"],
  arm: ["Why", "How", "Test"],
  hal: ["Why", "How", "Test"],
  auth: ["Why", "How", "Test", "Impact"],
  ota: ["Why", "How", "Test", "Impact"],
  config: ["Why", "What", "Impact"],
  harvest: ["Why", "What", "Impact"],
};
const BEHAVIOUR_TYPES = ["feat", "fix", "perf", "refactor"];
const PERF_LABELS = ["Why", "How", "Test"];

const LABEL_LINE = /^- ([A-Z][a-z]+): \S/;
const BREAKING_HEADER = /^\w+(\([^)]*\))?!: /;
const BREAKING_FOOTER = /^BREAKING[ -]CHANGE: \S/;

// Các dòng sau header, bỏ dòng chú thích mà git thêm vào khi mở editor.
const messageLines = (parsed) =>
  (parsed.raw ?? "").split(/\r?\n/).slice(1).filter((line) => !line.startsWith("#"));

function requiredLabels({ type, scope, header }) {
  const required = new Set();
  const byScope = LABELS_BY_SCOPE[scope];
  if (byScope) (BEHAVIOUR_TYPES.includes(type) ? byScope : ["Why"]).forEach((label) => required.add(label));
  if (type === "perf") PERF_LABELS.forEach((label) => required.add(label));
  if (BREAKING_HEADER.test(header ?? "")) required.add("Why");
  return required;
}

const localRules = {
  rules: {
    "body-labels": (parsed) => {
      if (parsed.type === "revert") return [true];
      const used = messageLines(parsed)
        .map((line) => LABEL_LINE.exec(line)?.[1])
        .filter((label) => LABELS.includes(label));
      const missing = [...requiredLabels(parsed)].filter((label) => !used.includes(label));
      if (missing.length > 0) {
        return [false, `body needs the labels ${missing.join(", ")} for this type and scope (see CONTRIBUTING.md)`];
      }
      const positions = used.map((label) => LABELS.indexOf(label));
      const inOrder = positions.every((position, i) => i === 0 || position > positions[i - 1]);
      return [inOrder, `body labels appear at most once each, in the order ${LABELS.join(", ")}`];
    },
    "breaking-marker": (parsed) => {
      const marked = BREAKING_HEADER.test(parsed.header ?? "");
      const noted = messageLines(parsed).some((line) => BREAKING_FOOTER.test(line));
      if (marked === noted) return [true];
      return [false, marked ? "a header with ! needs a BREAKING CHANGE: footer" : "a BREAKING CHANGE: footer needs ! in the header"];
    },
    // Commit revert được thêm đúng độ dài của tiền tố "revert: " vì header của nó chép header gốc.
    "header-length": (parsed, _when, { max, revertMax }) => {
      const limit = parsed.type === "revert" ? revertMax : max;
      const length = (parsed.header ?? "").length;
      return [length <= limit, `header is ${length} characters, the limit is ${limit}`];
    },
  },
};

export default {
  extends: ["@commitlint/config-conventional"],
  plugins: [localRules],
  rules: {
    "type-enum": [2, "always", ["build", "chore", "ci", "docs", "feat", "fix", "perf", "refactor", "revert", "style", "test"]],
    "scope-enum": [
      2,
      "always",
      ["api", "auth", "mission", "motion", "arm", "safety", "perception", "calib", "hal", "sim", "config", "recording",
        "harvest", "ota", "cli", "training", "hmi", "i18n", "deploy", "adr", "release", "deps", "deps-dev"],
    ],
    "subject-empty": [2, "never"],
    "subject-case": [2, "never", ["sentence-case", "start-case", "pascal-case", "upper-case"]],
    "subject-full-stop": [2, "never", "."],
    "header-max-length": [0],
    "header-length": [2, "always", { max: 72, revertMax: 80 }],
    "body-leading-blank": [2, "always"],
    "body-max-line-length": [2, "always", 100],
    "footer-leading-blank": [2, "always"],
    "footer-max-line-length": [2, "always", 100],
    "body-labels": [2, "always"],
    "breaking-marker": [2, "always"],
  },
};
