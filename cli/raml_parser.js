const raml = require("raml-parser");
const fs = require("fs");
const [ramlPath, jsonPath] = process.argv.slice(2);

if (!ramlPath || !jsonPath) {
  console.info("Usage: node raml_parser.js api.raml schema.json");
  process.exit(1);
}

raml
  .loadFile(ramlPath)
  .then(data => {
    // documentation isn't needed for validation
    delete data.documentation;
    fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2), "utf8");
  })
  .catch(err => {
    console.error(err);
    process.exit(1);
  });
