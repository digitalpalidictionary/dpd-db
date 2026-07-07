package tools

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
)

func ReadJsonSliceString(
	filePath string,
	object []string,
) []string {

	data, err := os.ReadFile(filePath)
	if err != nil {
		panic(err)
	}

	err = json.Unmarshal(data, &object)
	if err != nil {
		panic(err)
	}
	return object
}

func ReadJsonMapStringString(
	filePath string,
	object map[string]string,
) map[string]string {

	data, err := os.ReadFile(filePath)
	if err != nil {
		panic(err)
	}

	err = json.Unmarshal(data, &object)
	if err != nil {
		panic(err)
	}
	return object
}

func ReadJsonMapStringInt(
	filePath string,
	object map[string]int,
) map[string]int {

	data, err := os.ReadFile(filePath)
	if err != nil {
		panic(err)
	}

	err = json.Unmarshal(data, &object)
	if err != nil {
		panic(err)
	}
	return object
}

func ReadJsonMapStringMapStringInt(
	filePath string,
	object map[string]map[string]int,
) map[string]map[string]int {

	data, err := os.ReadFile(filePath)
	if err != nil {
		panic(err)
	}

	err = json.Unmarshal(data, &object)
	if err != nil {
		panic(err)
	}
	return object
}

// type bjtObject map[string][]map[string]map[string][]map[string]string

func ReadJsonBjt(
	filePath string,
	object map[string][]map[string]map[string][]map[string]string,
) map[string][]map[string]map[string][]map[string]string {
	data, err := os.ReadFile(filePath)
	HardCheck(err)

	err = json.Unmarshal(data, &object)
	HardCheck(err)
	return object
}

func ReadJsonSliceMapStringSliceString(
	filePath string,
	object []map[string][]string,
) []map[string][]string {

	data, err := os.ReadFile(filePath)
	if err != nil {
		pl(err)
		panic(err)
	}

	err = json.Unmarshal(data, &object)
	if err != nil {
		panic(err)
	}
	return object
}

func SaveJson(outputPath string, data any) bool {
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		fmt.Println(err)
		return false
	}
	err = os.WriteFile(outputPath, []byte(jsonData), os.ModePerm)
	if err != nil {
		fmt.Println(err)
		return false
	} else {
		return true
	}

}

// Indent 2 spaces & allow non-ascii characters
func JsonMarshall(data any) string {
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false) // Allow non-ASCII characters
	enc.SetIndent("", "")    // Set indentation to 0 spaces

	err := enc.Encode(data)
	HardCheck(err)

	return buf.String()
}
