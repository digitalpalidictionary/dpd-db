// transliterate the inflections into Devanagari, Sinhala and Thai using PathNirvana code

import { createRequire } from "module"
const require = createRequire(import.meta.url)
const fs = require('fs')

let json_input_path;
let json_output_path;

if (process.argv.length > 2) {
    json_input_path = process.argv[2];
    json_output_path = process.argv[3];
} else {
    json_input_path = './../share/inflections_to_translit.json';
    json_output_path = './../share/inflections_from_translit.json';
}

const changedInflections = require(json_input_path);

import { TextProcessor, Script } from './pali-script.mjs'

function toSinhala(text) {
	text = TextProcessor.basicConvertFrom(text, Script.RO)
	return text
}

function toDevanagari(text) {
	text = TextProcessor.basicConvert(text, Script.HI)
	return text
}

function toThai(text) {
	text = TextProcessor.basicConvert(text, Script.THAI)
	return text
}

for (let headword in changedInflections) {
	let sinhala = []
	let devanagari = []
	let thai = []

	let inflections = changedInflections[headword]["inflections"]
	
	for (let inflection of inflections) {
		let sinhala_word = toSinhala(inflection)
		sinhala.push(sinhala_word)
		devanagari.push(toDevanagari(sinhala_word))
		thai.push(toThai(sinhala_word))

	}
	changedInflections[headword]["sinhala"] = sinhala
	changedInflections[headword]["devanagari"] = devanagari
	changedInflections[headword]["thai"] = thai
}

let justInflectionsJson = JSON.stringify(changedInflections)
fs.writeFile(json_output_path, justInflectionsJson, function (err) {
	if (err) {
		console.log("An error occured while writing JSON Object to File.")
		return console.log(err)
	}
	console.log("ok")
})
