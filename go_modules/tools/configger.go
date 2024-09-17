package tools

import (
	"gopkg.in/ini.v1"
)

var configDotIni = "config.ini"

func iniLoad() *ini.File {
	iniFile, err := ini.Load(configDotIni)
	HardCheck(err)
	return iniFile
}

func IniRead(section string, key string) string {
	IniFile := iniLoad()
	return IniFile.Section(section).Key(key).String()
}

func IniTest(section string, key string, value string) bool {
	if IniRead(section, key) == value {
		return true
	} else {
		return false
	}
}

func IniSet(section string, key string, value string) {
	IniFile := iniLoad()
	IniFile.Section(section).Key(key).SetValue(value)
	err := IniFile.SaveTo(configDotIni)
	HardCheck(err)
}
