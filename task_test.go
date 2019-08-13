package main

import "testing"

// TestParseName confirms parsing of +project and other parameters
func TestParseName(t *testing.T) {
	tables := []struct {
		entry   string
		project string
		name    string
	}{
		{"Task with no project", "default", "Task with no project"},
		{"+project Task with project", "project", "Task with project"},
		{"Task with project +project", "project", "Task with project"},
		{"Task with project +PROJECT", "project", "Task with project"},
		//{ "Task with project +foo +project", "??", "Task with project"},
	}

	for _, table := range tables {
		p, n := parseEntry(table.entry)

		if p != table.project {
			t.Errorf("Expected: %s => Received: %s", table.project, p)
		}

		if n != table.name {
			t.Errorf("Expected: %s => Received: %s", table.name, n)
		}
	}

}
