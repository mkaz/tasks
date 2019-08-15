/**
 * task.go
 *
 * A simple command-line task list.
 */

package main

import (
	"flag"
	"fmt"
	"os"
	"os/user"
	"path/filepath"
	"strconv"
	"strings"
)

var taskDir string
var log Logger

func init() {
	log.DebugLevel = true

	usr, err := user.Current()
	log.FatalErrNotNil(err)
	// TODO: configurable
	taskDir = filepath.Join(usr.HomeDir, "Documents", "Sync", "tasks")
}

func main() {

	// parse command-line parameters
	var helpFlag = flag.Bool("help", false, "Display Help")

	// var today = flag.Bool("today", false, "Show todays task")
	// var week = flag.Bool("week", false, "Show last week tasks")
	// var from = flag.String("from", "", "Show tasks from date yyyy-mm-dd")
	// var to = flag.String("to", "", "Show tasks to date yyyy-mm-dd")
	// var search = flag.String("s", "", "Search for term")

	flag.Parse()
	args := flag.Args()

	if *helpFlag {
		usage()
	}

	if len(args) < 1 {
		showOpenTasks("")
		fmt.Println()
		os.Exit(0)
	}

	// check for +project as first arg
	// show tasks in project
	if strings.HasPrefix(args[0], "+") {
		showOpenTasks(args[0])
		os.Exit(0)
	}

	switch args[0] {

	case "add":
		entry := strings.Join(args[1:], " ")
		createNewTask(entry)

	case "done":
		taskID := getTaskID(args[1])
		markTaskDone(taskID)

	case "note":
		taskID := getTaskID(args[1])
		note := strings.Join(args[2:], " ")
		addNoteToTask(taskID, note)

	case "report":
		filter := ""
		if len(args) > 1 {
			filter = args[1]
		}
		showCompletedReport(filter)

	case "delete":
		taskID := getTaskID(args[1])
		deleteTask(taskID)

	default:
		usage()
	}

}

func getTaskID(arg string) int {
	taskID, err := strconv.Atoi(arg)
	log.FatalErrNotNil(err, "Invalid task id")
	return taskID
}

// Display Usage
func usage() {
	fmt.Println("usage: task [flags] [command] [id] [text]")
	fmt.Println(`Commands:
	add
		Add new task, [text] required
	done
		Mark task as done, [id] required
	note
		Add note to task, [id] and [text] required
	delete
		Delete task, [id] required
	report
		Show completed tasks, [+project] optional
	`)
	fmt.Println("Flags:")
	flag.PrintDefaults()
	os.Exit(0)
}
