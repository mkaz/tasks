package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// Task is the primary task data structure
type Task struct {
	ID             int
	Name           string
	Project        string
	Filename       string `toml:"-"`
	Notes          []Note `toml:"Notes,omitempty"`
	CreationDate   time.Time
	CompletionDate time.Time
}

// Note is a note struct for a Task
type Note struct {
	CreationDate time.Time
	Entry        string
}

func createNewTask(entry string) {
	project, name := parseEntry(entry)
	task := Task{
		ID:           getNewTaskID(),
		Name:         name,
		Project:      project,
		CreationDate: time.Now(),
	}
	task.Save()
	fmt.Printf("Task ID %d created\n", task.ID)
}

func addNoteToTask(taskID int, note string) {
	task, err := getTaskByID(taskID)
	log.FatalErrNotNil(err, "Task not found")
	task.Notes = append(task.Notes, Note{Entry: note, CreationDate: time.Now()})
	task.Save()
	fmt.Println("Note added to", task.ID)
}

// markTaskDone receives task id as input and marks as
// done by renaming the file - just need to find the project :-/
func markTaskDone(taskID int, note string) {
	task, err := getTaskByID(taskID)
	log.FatalErrNotNil(err, "Task not found")
	if note != "" {
		task.Notes = append(task.Notes, Note{Entry: note, CreationDate: time.Now()})
	}
	task.CompletionDate = time.Now()
	task.Save()

	doneFilename := filepath.Join(filepath.Dir(task.Filename), fmt.Sprintf("%d.done.toml", task.ID))
	os.Rename(task.Filename, doneFilename)
	fmt.Printf("Marked %d as done\n", task.ID)
}

func deleteTask(taskID int) {
	task, err := getTaskByID(taskID)
	log.FatalErrNotNil(err, "Task not found")
	task.Delete()
	fmt.Printf("Task %d deleted\n", task.ID)
}

func openTaskInEditor(taskID int) {
	task, err := getTaskByID(taskID)
	log.FatalErrNotNil(err, "Task not found")
	cmd := exec.Command("vim", task.getFilename())
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Run()
}

// parseEntry receives entry from command line and parses it
// returning the project and name
func parseEntry(entry string) (project, name string) {
	var a []string

	if !strings.Contains(entry, "+") {
		return "default", entry
	}
	// split on whitespace, project = first item with +
	words := strings.Split(entry, " ")
	for _, word := range words {
		if strings.HasPrefix(word, "+") {
			project = strings.ToLower(word[1:])
		} else {
			a = append(a, word)
		}
	}
	name = strings.Join(a, " ")

	return
}
