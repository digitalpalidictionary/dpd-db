package tools

import (
	"encoding/csv"
	"os"
	"strings"
)

func SaveTsv(
	filePath string, separator string, header []string, data [][]string) {

	file, err := os.Create(filePath)
	HardCheck(err)

	df := csv.NewWriter(file)
	df.Comma = []rune(separator)[0]

	err = df.Write(header)
	HardCheck(err)

	err = df.WriteAll(data)
	HardCheck(err)

	file.Close()
}

func ReadText(filePath string) []string {

	data, err := os.ReadFile(filePath)
	HardCheck(err)
	return strings.Split((string(data)), "\n")
}

func ReadTsv(filePath string) []map[string]string {

	rawData, err := os.ReadFile(filePath)
	if err != nil {
		pl(err)
		return nil
	} else {
		data := data_to_slice_map(rawData)
		return data
	}
}

func data_to_slice_map(data []byte) []map[string]string {
	text := string(data)
	text_lines := strings.Split(text, "\n")

	// return is a slice of maps
	// columnName : columnValue
	var sliceMap = []map[string]string{}
	var header []string

	for index, value := range text_lines {

		// each line has multiple tab separated values
		textLineSplit := strings.Split(value, "\t")
		textLineLen := len(textLineSplit)

		// make a map as long as the number of values
		m := make(map[string]string, textLineLen)

		// assume line 0 is a header
		if index == 0 {
			header = textLineSplit

		} else {
			// make key value pairs and append to the slice
			if len(textLineSplit) > 1 {
				for lIndex, lValue := range textLineSplit {
					m[header[lIndex]] = lValue

				}
				sliceMap = append(sliceMap, m)
			}

		}
	}

	return sliceMap
}
