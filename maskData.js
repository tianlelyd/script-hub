const fs = require("fs");
const yaml = require("js-yaml");
const maskData = require("maskdata");
const { Command } = require("commander");

// 读取文件
const readFile = (filePath) => {
  return fs.readFileSync(filePath, "utf8");
};

// 写入文件
const writeFile = (filePath, data) => {
  fs.writeFileSync(filePath, data, "utf8");
};

// 脱敏处理函数
const maskSensitiveData = (data) => {
  const maskOptions = {
    maskWith: "*",
    unmaskedStartDigits: 2,
    unmaskedEndDigits: 2,
  };

  if (typeof data === "string") {
    return maskData.maskPhone(data, maskOptions); // 假设数据为电话号码
  }

  if (typeof data === "object") {
    for (let key in data) {
      if (typeof data[key] === "string") {
        data[key] = maskData.maskPhone(data[key], maskOptions);
      } else if (typeof data[key] === "object") {
        data[key] = maskSensitiveData(data[key]);
      }
    }
  }

  return data;
};

// 处理YAML数据
const processYAML = (inputFilePath, outputFilePath) => {
  const fileContents = readFile(inputFilePath);
  let data = yaml.load(fileContents);
  data = maskSensitiveData(data);
  const yamlStr = yaml.dump(data);
  writeFile(outputFilePath, yamlStr);
};

// 处理JSON数据
const processJSON = (inputFilePath, outputFilePath) => {
  const fileContents = readFile(inputFilePath);
  let data = JSON.parse(fileContents);
  data = maskSensitiveData(data);
  const jsonStr = JSON.stringify(data, null, 2);
  writeFile(outputFilePath, jsonStr);
};

// 主函数
const main = () => {
  const program = new Command();

  program
    .option("-f, --file <path>", "path to the input file")
    .option("-o, --output <path>", "path to the output file")
    .option(
      "-t, --type <type>",
      "type of the file (yaml or json)",
      /^(yaml|json)$/i,
      "json"
    )
    .parse(process.argv);

  const options = program.opts();

  if (!options.file || !options.output) {
    console.error("Input and output file paths are required.");
    process.exit(1);
  }

  if (options.type === "yaml") {
    processYAML(options.file, options.output);
  } else if (options.type === "json") {
    processJSON(options.file, options.output);
  } else {
    console.error('Invalid file type specified. Use "yaml" or "json".');
    process.exit(1);
  }

  console.log(`Data masking completed for ${options.type.toUpperCase()} file.`);
};

main();
