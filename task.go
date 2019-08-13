package main

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"strconv"
	"time"

	"github.com/BurntSushi/toml"
)

// Task is the primary task data structure
type Task struct {
	ID           int
	Name         string
	Project      string
	CreationDate time.Time
}

// Save task to disk
func (t Task) Save() {
	t.makeProjectDirectory()
	buf := new(bytes.Buffer)
	err := toml.NewEncoder(buf).Encode(t)
	log.FatalErrNotNil(err, "Saving Task to File")
	ioutil.WriteFile(t.getTaskFilename(), buf.Bytes(), 0644)
}

func (t Task) makeProjectDirectory() {
	// check if project directory exists
	dirpath := filepath.Join(taskDir, t.Project)
	if _, err := os.Stat(dirpath); os.IsNotExist(err) {
		log.Debug("Project direcotry does not exist, creating")
		err := os.Mkdir(dirpath, 0755)
		log.FatalErrNotNil(err, "Making project directory")
	}
}
func (t Task) getTaskFilename() string {
	return filepath.Join(taskDir, t.Project, strconv.Itoa(t.ID)+".toml")
}

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

func createNewTask(name string) {
	// TODO: parse for project
	project := "default"
	task := Task{
		ID:           getNewTaskID(),
		Name:         name,
		Project:      project,
		CreationDate: time.Now(),
	}
	task.Save()
	fmt.Printf("Task ID %d created\n", task.ID)
}
