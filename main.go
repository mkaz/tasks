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

	if len(args) < 2 {
		fmt.Println(">> Not enough args")
		os.Exit(0)
	}

	switch args[0] {

	case "add":
		entry := strings.Join(args[1:], " ")
		createNewTask(entry)
	case "delete":
		taskID, err := strconv.Atoi(args[1])
		if err != nil {
			fmt.Println("Invalid task id")
			os.Exit(1)
		}
		// TODO:
		fmt.Printf("Deleting %d\n", taskID)

	default:
		usage()
	}

}

// Display Usage
func usage() {
	fmt.Println("usage: task [command] [id] [text]")
	fmt.Println("Args:")
	flag.PrintDefaults()
	os.Exit(0)
}
