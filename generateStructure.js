const fs = require("fs");
const path = require("path");

const excludedDirs = [
  "node_modules",
  ".next",
  ".vercel",
  ".vscode",
  ".wrangler",
  ".git",
  "dist",
];
const rootDir = process.argv[2] || __dirname;
const outputFile = path.join(rootDir, "structure.txt");

function generateTree(dir, indent = "") {
  let tree = "";
  const items = fs
    .readdirSync(dir)
    .filter((item) => !excludedDirs.includes(item));

  items.forEach((item, index) => {
    const fullPath = path.join(dir, item);
    const isLast = index === items.length - 1;
    const isDirectory = fs.lstatSync(fullPath).isDirectory();
    const prefix = isLast ? "└─" : "├─";
    const childIndent = isLast ? "  " : "│ ";

    if (isDirectory) {
      tree += `${indent}${prefix}📂 ${item}\n`;
      tree += generateTree(fullPath, indent + childIndent);
    } else {
      tree += `${indent}${prefix}📜 ${item}\n`;
    }
  });

  return tree;
}

const treeStructure = `📦 ${path.basename(rootDir)}\n${generateTree(rootDir)}`;
fs.writeFileSync(outputFile, treeStructure);
console.log(`Directory structure has been saved to ${outputFile}`);
