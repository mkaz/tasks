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

	"github.com/BurntSushi/toml"
)

const version = "1.0.0"

var log Logger

// TaskConfig is struct for holding config settings
type TaskConfig struct {
	TaskDir string
}

var tc TaskConfig

// Display Usage
func usage() {
	fmt.Printf("Task v%s\n", version)
	fmt.Println("")
	fmt.Println("USAGE: task [flags] [command] [id] [text]")
	fmt.Println(`
COMMANDS:
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

	fmt.Println("FLAGS:")
	flag.PrintDefaults()
	fmt.Println(`

CONFIGURATION:

  Task requires a directory to be set to store task files

  The task directory can be set:
	Option 1: Use --task-dir DIR flag on command-line
	Option 2: Create task.conf in XDG_CONFIG_DIR
	Option 3: Create $HOME/.task.conf

  The config file uses TOML format and requires TaskDir set
  Example:
	TaskDir='/home/username/Documents/tasks'
 `)
	os.Exit(0)
}

func init() {
	// parse command-line parameters
	var helpFlag = flag.Bool("help", false, "Display Help")
	var debugFlag = flag.Bool("debug", false, "Display extra info")
	var quietFlag = flag.Bool("quiet", false, "Display less info")
	var versionFlag = flag.Bool("version", false, "Display version")

	var taskDirFlag = flag.String("task-dir", "", "Set task directory")

	// var today = flag.Bool("today", false, "Show todays task")
	// var week = flag.Bool("week", false, "Show last week tasks")
	// var from = flag.String("from", "", "Show tasks from date yyyy-mm-dd")
	// var to = flag.String("to", "", "Show tasks to date yyyy-mm-dd")
	// var search = flag.String("s", "", "Search for term")
	flag.Parse()

	if *helpFlag {
		usage()
	}

	if *versionFlag {
		fmt.Printf("Task v%s\n", version)
		os.Exit(0)
	}

	// configure logger based on flag
	log.DebugLevel = *debugFlag
	log.Quiet = *quietFlag

	tc.TaskDir = getTaskDir(*taskDirFlag)
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

// getConfigFile determines the location of the config file
// Using XDG_CONFIG_DIR and HOME environment variables
func getConfigFile() (configFile string) {

	xdg := os.Getenv("XDG_CONFIG_DIR")
	if xdg != "" {
		return filepath.Join(xdg, "task.conf")
	}

	usr, err := user.Current()
	if err != nil {
		log.Fatal("Error getting current user")
	}

	// check if .config dir exists
	configDir := filepath.Join(usr.HomeDir, ".config")
	if _, err := os.Stat(configDir); os.IsExist(err) {
		return filepath.Join(configDir, "task.conf")
	}

	// TODO: Windows
	// TODO: Mac

	return filepath.Join(usr.HomeDir, ".task.conf")

}

// getTaskDirFromConfig gets config file and
// reads in task directory
func getTaskDirFromConfig() string {
	var taskConfig TaskConfig
	configFile := getConfigFile()
	log.Debug("Reading config from:", configFile)
	if _, err := os.Stat(configFile); os.IsNotExist(err) {
		log.Warn("Configuration file does not exist", configFile)
	}

	// read in configuration file
	_, err := toml.DecodeFile(configFile, &taskConfig)
	log.FatalErrNotNil(err, "Error decoding config file", configFile)

	if taskConfig.TaskDir == "" {
		log.Fatal("Error: TaskDir parameter not set in ", configFile)
	}
	return taskConfig.TaskDir
}

// getTaskDir accepts passed directory from flags
// reads in configuration settings, or sets default
// confirms directory exists
func getTaskDir(dir string) string {
	if dir == "" {
		dir = getTaskDirFromConfig()
	}

	// check that task directory exists
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		log.Fatal("Task directory not found", dir)
	}

	return dir
}
