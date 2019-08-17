package main

import (
	"fmt"
	"strings"
	"testing"
)

// TestParseName confirms parsing of +project and other parameters
func TestCLIParams(t *testing.T) {
	tables := []struct {
		entry   string
		command string
		taskID  int
		extra   string
	}{
		{"add Task with no project", "add", 0, "Task with no project"},
		{"delete 10 extra note", "delete", 10, "extra note"},
		{"10 delete extra note", "delete", 10, "extra note"},
		{"edit 1", "edit", 1, ""},
		{"1 edit", "edit", 1, ""},
		{"done 4 extra note", "done", 4, "extra note"},
		{"4 done extra note", "done", 4, "extra note"},
		
	}

	for _, table := range tables {
		fmt.Println("Testing: ",table.entry)
		cmd, id, str := parseCommandArgs(strings.Split(table.entry, " "))

		if cmd != table.command {
			t.Errorf("Expected: %s => Received: %s", table.command, cmd)
		}

		if id != table.taskID {
			
			t.Errorf("Expected: %d => Received: %d", table.taskID, id)
		}

		if str != table.extra {
			t.Errorf("Expected: %s => Received: %s", table.extra, str)
		}
	}

}
