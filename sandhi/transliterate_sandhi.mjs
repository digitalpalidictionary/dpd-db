// transliterate deconstructor results using PathNirvana code

let c = console.log
import { createRequire } from "module"
const require = createRequire(import.meta.url)
const sandhiDict = require('./../share/sandhi_to_translit.json')
const fs = require('fs')

import { TextProcessor, Script, paliScriptInfo, getScriptForCode } from '../inflections/pali-script.mjs'

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

for (let headword in sandhiDict) {
	let sinhala = []
	let devanagari = []
	let thai = []

	let sandhi = sandhiDict[headword]["sandhi"]
	
    let sinhala_word = toSinhala(sandhi)
    sinhala.push(sinhala_word)
    devanagari.push(toDevanagari(sinhala_word))
    thai.push(toThai(sinhala_word))

	sandhiDict[headword]["sinhala"] = sinhala
	sandhiDict[headword]["devanagari"] = devanagari
	sandhiDict[headword]["thai"] = thai
}

let justInflectionsJson = JSON.stringify(sandhiDict)
fs.writeFile("share/sandhi_from_translit.json", justInflectionsJson, function (err) {
	if (err) {
		console.log("An error occured while writing JSON Object to File.")
		return console.log(err)
	}
	console.log("ok")
})