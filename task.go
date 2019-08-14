package main

import (
	"bytes"
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/BurntSushi/toml"
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

type Note struct {
	CreationDate time.Time
	Entry        string
}

// Save task to disk
func (t Task) Save() {
	t.makeProjectDirectory()
	buf := new(bytes.Buffer)
	err := toml.NewEncoder(buf).Encode(t)
	log.FatalErrNotNil(err, "Saving Task to File")
	ioutil.WriteFile(t.getTaskFilename(), buf.Bytes(), 0644)
}

// makeProjectDirectory checks to see if project directory exists
// creates new directory if it does not exist
func (t Task) makeProjectDirectory() {
	// check if project directory exists
	dirpath := filepath.Join(taskDir, t.Project)
	if _, err := os.Stat(dirpath); os.IsNotExist(err) {
		log.Debug("Project directory does not exist, creating")
		err := os.Mkdir(dirpath, 0755)
		log.FatalErrNotNil(err, "Making project directory")
	}
}

// getTaskFilename returns the filename
func (t Task) getTaskFilename() string {
	return filepath.Join(taskDir, t.Project, strconv.Itoa(t.ID)+".toml")
}

// getNewTaskID reads the task-id file increments and returns new id
// if task-id file is not found, it will create and return 1
func getNewTaskID() int {

	// read from file
	filename := filepath.Join(taskDir, "task-id")

	// check if file exists
	if _, err := os.Stat(filename); os.IsNotExist(err) {
		log.Debug("No task id file")
		ioutil.WriteFile(filename, []byte(strconv.Itoa(1)), 0644)
		return 1
	}

	content, err := ioutil.ReadFile(filename)
	log.FatalErrNotNil(err, "Reading task-id file")
	taskID, err := strconv.Atoi(string(content))
	if err != nil {
		log.Warn("task-id file exists, but invalid ID")
		taskID = 0
	}

	// increment
	taskID = taskID + 1

	// save to file
	ioutil.WriteFile(filename, []byte(strconv.Itoa(taskID)), 0644)

	return taskID
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
	task, err := getTaskById(taskID)
	log.FatalErrNotNil(err, "Task not found")
	task.Notes = append(task.Notes, Note{Entry: note, CreationDate: time.Now()})
	task.Save()
	fmt.Println("Note added to", task.ID)
}

// markTaskDone receives task id as input and marks as
// done by renaming the file - just need to find the project :-/
func markTaskDone(taskID int) {
	task, err := getTaskById(taskID)
	log.FatalErrNotNil(err, "Task not found")

	doneFilename := filepath.Join(filepath.Dir(task.Filename), fmt.Sprintf("%d.done.toml", task.ID))
	os.Rename(task.Filename, doneFilename)
	fmt.Printf("Marked %d as done\n", task.ID)
}

func getTaskById(taskID int) (Task, error) {
	var fullFilepath string
	filename := fmt.Sprintf("%d.toml", taskID)
	err := filepath.Walk(taskDir, func(fn string, fi os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !fi.IsDir() {
			if filepath.Base(fn) == filename {
				fullFilepath = fn
				// fmt.Println("Found", fullFilepath)
				return io.EOF
			}
		}
		return nil
	})
	if err == io.EOF {
		err = nil
	}
	log.FatalErrNotNil(err, "Error finding task")
	return readTaskFromFilename(fullFilepath)
}

func readTaskFromFilename(filename string) (task Task, err error) {
	_, err = toml.DecodeFile(filename, &task)
	log.WarnErrNotNil(err, "Error decoding file")
	task.Filename = filename
	return
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
