var raml = require('raml-parser');
var fs = require('fs');


raml.loadFile('index.raml').then( function(data) {
        fs.writeFile('schema.json', JSON.stringify(data, null, 2), function (err) {
            if (err)
                return console.log(err);
            console.log('Converted RAML to JSON in `schema.json`.');
        });
    }, function(error) {
        console.log('Error parsing: ' + error);
    });
