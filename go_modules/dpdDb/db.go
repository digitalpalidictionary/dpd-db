package dpdDb

import (
	"dpd/go_modules/tools"
	"path/filepath"

	_ "github.com/mattn/go-sqlite3"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

// Usage:
//
//	db := GetDb()
//	var result []DpdHeadword
//	err := db.Find(&result)
//	tools.Check(err.Error)
func GetDb() *gorm.DB {
	var dbPath = filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.DpdDb,
	)
	// db, err := gorm.Open(sqlite.Open(dbPath), &gorm.Config{})
	db, err := gorm.Open(sqlite.Open(dbPath), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Error),
	})
	tools.HardCheck(err)
	return db
}

func Rollback(tx *gorm.DB) {
	if r := recover(); r != nil {
		tx.Rollback()
	}
}

// Usage:
//
//	db, results := db.GetDpdHeadword()
//	for index, i := range results {
//		pl(index, i.ID, i.Lemma1)
//	}
func GetDpdHeadword() (*gorm.DB, []DpdHeadword) {
	db := GetDb()
	var results []DpdHeadword
	err := db.Find(&results)
	tools.HardCheck(err.Error)
	return db, results
}

func GetColumns(columns []string) (*gorm.DB, []DpdHeadword) {
	db := GetDb()

	var results []DpdHeadword
	err := db.Select(columns).Find(&results)
	tools.HardCheck(err.Error)

	return db, results
}

// Example of a Select and Where statement.
func GetSelectWhere() (*gorm.DB, []DpdHeadword) {
	db := GetDb()

	var results []DpdHeadword
	err := db.Select("id", "lemma_1", "pos").
		Where("pos = ?", "abbrev").
		Find(&results)
	tools.HardCheck(err.Error)

	return db, results
}

// Update a single column in dpdHeadwords.
// Takes 1m44s
func UpdateHeadwordSingleColumn(
	db *gorm.DB, id int, columnName string, columnValue string) *gorm.DB {
	return db.Model(&DpdHeadword{}).Where("id = ?", id).UpdateColumn(columnName, columnValue)
}

// Update a single column in dpdHeadwords with an int value
func UpdateHeadwordSingleColumnInt(
	db *gorm.DB, id int, columnName string, columnValue int) *gorm.DB {
	return db.Model(&DpdHeadword{}).Where("id = ?", id).UpdateColumn(columnName, columnValue)
}

func GetLookup() (*gorm.DB, []Lookup) {
	db := GetDb()
	var results []Lookup
	err := db.Find(&results)
	tools.HardCheck(err.Error)
	return db, results
}

// Update a single column in Lookup.
// takes 12min50sec! too slow!
func UpdateLookupDeconstructor(
	db *gorm.DB, key, value string) *gorm.DB {
	return db.Model(&Lookup{}).Where("lookup_key = ?", key).UpdateColumn("deconstructor", value)
}

// Some others ways to update the db

// This takes about 2m01s
// err := db.Transaction(func(tx *gorm.DB) error {
// 	return tx.Save(i).Error
// })
// tools.Check(err)

// Also 2m00s
// tx := db.Save(i)
// tools.Check(tx.Error)
