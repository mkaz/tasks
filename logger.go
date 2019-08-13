package main

import (
	"fmt"
	"os"

	"github.com/ttacon/chalk"
)

// Logger is a logging type
type Logger struct {
	DebugLevel bool
	Quiet      bool
}

// Debug prints out if debug level set
func (l Logger) Debug(a ...interface{}) {
	if l.DebugLevel {
		fmt.Println(chalk.Cyan, a, chalk.Reset)
	}
}

// Info prints out if not quiet
func (l Logger) Info(a ...interface{}) {
	if l.DebugLevel || !l.Quiet {
		fmt.Println(chalk.Green, a, chalk.Reset)
	}
}

// Warn always prints out
func (l Logger) Warn(a ...interface{}) {
	fmt.Println(chalk.Yellow, a, chalk.Reset)
}

// Fatal always prints out and exists err=1
func (l Logger) Fatal(a ...interface{}) {
	fmt.Println(chalk.Red, a, chalk.Reset)
	os.Exit(1)
}

// FatalErrNotNil checks err value and prints and exits if not nil
func (l Logger) FatalErrNotNil(err error, a ...interface{}) {
	if err != nil {
		fmt.Println(chalk.Red, a, chalk.Reset)
		os.Exit(1)
	}
}
