import fs from "node:fs";
import path from "node:path";

const baseDir = process.cwd();
const targetDir = path.join(baseDir, "node_modules", "expo-module-scripts");
const sourceFile = path.join(targetDir, "tsconfig.base.json");
const shimFile = path.join(targetDir, "tsconfig.base");

try {
  if (!fs.existsSync(sourceFile)) {
    process.exit(0);
  }

  if (!fs.existsSync(shimFile)) {
    fs.writeFileSync(shimFile, '{"extends":"./tsconfig.base.json"}\n', "utf8");
  }
} catch (_error) {
  // Do not fail install for this shim.
}
