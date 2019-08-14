package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/dustin/go-humanize"
	"github.com/ttacon/chalk"
)

func displayOpenTasks() {
	fmt.Printf("  %s : %-10s : %-50s : %s\n", "ID", "Project", "Task", "Age")
	fmt.Println("-----:------------:----------------------------------------------------:---------------")
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

// displayTaskFromFile reads a task file and displays an entry
// TODO: truncate project, name to fit display if too long
func displayTaskFromFile(filename string) {
	task, err := readTaskFromFilename(filename)
	if err == nil {
		fmt.Print(getColorForProject(task.Project))
		fmt.Printf("%4d : %-10s : %-50s : %s\n", task.ID, task.Project, task.Name, humanize.Time(task.CreationDate))
		fmt.Print(chalk.Reset)
	}
}

func getColorForProject(project string) chalk.Color {
	val := 0
	colors := []chalk.Color{
		chalk.Green, chalk.Yellow, chalk.Blue, chalk.Magenta, chalk.Cyan,
	}

	for _, s := range project {
		val = val + int(s)
	}

	index := val % len(colors)
	return colors[index]
}
