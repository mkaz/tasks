package main

import (
	"bytes"
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"path/filepath"
	"strconv"

	"github.com/BurntSushi/toml"
)

// Save task to disk
func (t Task) Save() {
	t.makeProjectDirectory()
	buf := new(bytes.Buffer)
	err := toml.NewEncoder(buf).Encode(t)
	log.FatalErrNotNil(err, "Saving Task to File")
	ioutil.WriteFile(t.getFilename(), buf.Bytes(), 0644)
}

// Delete task from disk
func (t Task) Delete() error {
	filename := t.getFilename()
	if _, err := os.Stat(filename); os.IsNotExist(err) {
		log.Warn("Task file does not exist")
		return err
	}
	return os.Remove(filename)
}

// makeProjectDirectory checks to see if project directory exists
// creates new directory if it does not exist
func (t Task) makeProjectDirectory() {
	// check if project directory exists
	dirpath := filepath.Join(tc.TaskDir, t.Project)
	if _, err := os.Stat(dirpath); os.IsNotExist(err) {
		log.Debug("Project directory does not exist, creating")
		err := os.Mkdir(dirpath, 0755)
		log.FatalErrNotNil(err, "Making project directory")
	}
}

// getFilename returns the filename
func (t Task) getFilename() string {
	return filepath.Join(tc.TaskDir, t.Project, strconv.Itoa(t.ID)+".toml")
}

// getNewTaskID reads the task-id file increments and returns new id
// if task-id file is not found, it will create and return 1
func getNewTaskID() int {

	// read from file
	filename := filepath.Join(tc.TaskDir, "task-id")

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

func getTaskByID(taskID int) (Task, error) {
	var fullFilepath string
	f1 := fmt.Sprintf("%d.toml", taskID)
	f2 := fmt.Sprintf("%d.done.toml", taskID)
	err := filepath.Walk(tc.TaskDir, func(fn string, fi os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !fi.IsDir() {
			if filepath.Base(fn) == f1 || filepath.Base(fn) == f2 {
				fullFilepath = fn
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
