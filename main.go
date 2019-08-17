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
	show
		Show task details, [id] required
	edit
		Open task in editor, [id] required
	delete
		Delete task, [id] required
	report
		Show completed tasks, [+project] optional
	`)
	fmt.Println("Flags:")
	flag.PrintDefaults()
	os.Exit(0)
}

func init() {
	// parse command-line parameters
	var helpFlag = flag.Bool("help", false, "Display Help")
	var debugFlag = flag.Bool("debug", false, "Display extra info")
	var quietFlag = flag.Bool("quiet", false, "Display less info")

	// var today = flag.Bool("today", false, "Show todays task")
	// var week = flag.Bool("week", false, "Show last week tasks")
	// var from = flag.String("from", "", "Show tasks from date yyyy-mm-dd")
	// var to = flag.String("to", "", "Show tasks to date yyyy-mm-dd")
	// var search = flag.String("s", "", "Search for term")
	flag.Parse()

	if *helpFlag {
		usage()
	}

	// configure logger based on flag
	log.DebugLevel = *debugFlag
	log.Quiet = *quietFlag

	usr, err := user.Current()
	log.FatalErrNotNil(err)

	// TODO: configurable
	taskDir = filepath.Join(usr.HomeDir, "Documents", "Sync", "tasks")
}

// nolint: gocyclo
func main() {

	args := flag.Args()

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

	cmd, taskID, extra := parseCommandArgs(args)

	switch cmd {

	case "add":
		createNewTask(extra)

	case "report":
		showCompletedReport(extra)

	case "done":
		markTaskDone(taskID, extra)

	case "note":
		addNoteToTask(taskID, extra)

	case "show":
		showTask(taskID)

	case "edit":
		openTaskInEditor(taskID)

	case "delete":
		deleteTask(taskID)

	default:
		usage()
	}

}

// parseCommand arguments into command, id, and extra
// By default:
//		args[0] = command
//      args[1] = task id
// But, lets be flexible if args[0] is an int
// lets allow args[1] to be command
func parseCommandArgs(args []string) (cmd string, taskID int, extra string) {
	// check if args[0] is int
	if _, err := strconv.Atoi(args[0]); err == nil {
		taskID = getTaskID(args[0])
		cmd = args[1]
		if len(args) > 2 {
			extra = strings.Join(args[2:], " ")
		}
	} else {
		cmd = args[0]
		if cmd == "add" || cmd == "report" {
			extra = strings.Join(args[1:], " ")
		} else {
			taskID = getTaskID(args[1])
			if len(args) > 2 {
				extra = strings.Join(args[2:], " ")
			}
		}
	}

	return
}

func getTaskID(arg string) int {
	taskID, err := strconv.Atoi(arg)
	log.FatalErrNotNil(err, "Invalid task id")
	return taskID
}
