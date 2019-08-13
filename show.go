package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/BurntSushi/toml"
	"github.com/dustin/go-humanize"
)

func displayOpenTasks() {
	fmt.Printf(" %s : %-50s %s\n", "ID", "Task", "Age")
	filepath.Walk(taskDir, func(fn string, fi os.FileInfo, err error) error {
		if err != nil {
			log.Warn("Open tasks walk", err)
			return err
		}
		if !fi.IsDir() {
			if filepath.Ext(fn) == ".toml" {
				if !strings.Contains(fn, ".done") {
					displayTaskFromFile(fn)
				}
			}
		}
		return nil
	})
}

func displayTaskFromFile(filename string) {
	var task Task

	if _, err := toml.DecodeFile(filename, &task); err != nil {
		log.Warn("Error decoding file", err)
		return
	}

	fmt.Printf("%4d: %-50s %s\n", task.ID, task.Name, humanize.Time(task.CreationDate))
}
