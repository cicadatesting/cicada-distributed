package scheduling

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/sirupsen/logrus"
)

type LocalScheduler struct {
	client *execClient
}

type LocalSchedulingMetadata struct {
	PythonExecutable string `json:"pythonExecutable"`
	TestFilePath     string `json:"testFilePath"`
	Logdir           string `json:"logdir"`
}

func NewLocalScheduler() *LocalScheduler {
	return &LocalScheduler{client: newExecClient()}
}

func (ls *LocalScheduler) Teardown() error {
	return ls.client.teardown()
}

func (ls *LocalScheduler) CreateTest(testID, backendAddress, schedulingMetadata string, tags []string) error {
	localSchedulingMetadata := LocalSchedulingMetadata{}

	err := json.Unmarshal([]byte(schedulingMetadata), &localSchedulingMetadata)

	if err != nil {
		return fmt.Errorf("Error loading scheduling metadata: %v", err)
	}

	tagArg := GetTagArg(tags)

	err = ls.client.startTestProcess(
		testID,
		localSchedulingMetadata.Logdir,
		append([]string{
			localSchedulingMetadata.PythonExecutable,
			"-u",
			localSchedulingMetadata.TestFilePath,
			"run-test",
			"--test-id",
			testID,
			"--backend-address",
			backendAddress,
		}, tagArg...),
		map[string]string{},
	)

	if err != nil {
		return fmt.Errorf("Error starting test: %v", err)
	}

	return nil
}

func (ls *LocalScheduler) CreateScenario(
	testID,
	scenarioID,
	scenarioName,
	backendAddress,
	schedulingMetadata,
	encodedContext string,
) error {
	localSchedulingMetadata := LocalSchedulingMetadata{}

	err := json.Unmarshal([]byte(schedulingMetadata), &localSchedulingMetadata)

	if err != nil {
		return fmt.Errorf("Error loading scheduling metadata: %v", err)
	}

	err = ls.client.startTestProcess(
		scenarioID,
		localSchedulingMetadata.Logdir,
		[]string{
			localSchedulingMetadata.PythonExecutable,
			"-u",
			localSchedulingMetadata.TestFilePath,
			"run-scenario",
			"--name",
			scenarioName,
			"--test-id",
			testID,
			"--scenario-id",
			scenarioID,
			"--encoded-context",
			encodedContext,
			"--backend-address",
			backendAddress,
		},
		map[string]string{},
	)

	if err != nil {
		return fmt.Errorf("Error starting scenario: %v", err)
	}

	return nil
}

func (ls *LocalScheduler) CreateUserManagers(
	userManagerIDs []string,
	testID, scenarioName, backendAddress, schedulingMetadata, encodedContext string,
) error {
	localSchedulingMetadata := LocalSchedulingMetadata{}

	err := json.Unmarshal([]byte(schedulingMetadata), &localSchedulingMetadata)

	if err != nil {
		return fmt.Errorf("Error loading scheduling metadata: %v", err)
	}

	for _, userManagerID := range userManagerIDs {
		err := ls.client.startTestProcess(
			userManagerID,
			localSchedulingMetadata.Logdir,
			[]string{
				localSchedulingMetadata.PythonExecutable,
				"-u",
				localSchedulingMetadata.TestFilePath,
				"run-user",
				"--name",
				scenarioName,
				"--user-manager-id",
				userManagerID,
				"--backend-address",
				backendAddress,
				"--encoded-context",
				encodedContext,
			},
			map[string]string{},
		)

		if err != nil {
			return fmt.Errorf("Error starting test: %v", err)
		}
	}

	return nil
}

func (ls *LocalScheduler) StopUserManagers(userManagerIDs []string, schedulingMetadata string) error {
	for _, userManagerID := range userManagerIDs {
		err := ls.client.stopTestProcess(userManagerID)

		if err != nil {
			return fmt.Errorf("Error stopping user manager: %v", err)
		}
	}

	return nil
}

func (ls *LocalScheduler) CleanTestInstances(testID, schedulingMetadata string) error {
	err := ls.client.stopTestProcess(testID)

	if err != nil {
		return fmt.Errorf("Error stopping test instances: %v", err)
	}

	return nil
}

type execClient struct {
	processes map[string]*exec.Cmd
	logfiles  map[string]*os.File
}

func newExecClient() *execClient {
	return &execClient{
		processes: make(map[string]*exec.Cmd),
		logfiles:  make(map[string]*os.File),
	}
}

func (ec *execClient) teardown() error {
	errors := []string{}

	for name, cmd := range ec.processes {
		err := cmd.Process.Kill()

		if err != nil {
			errors = append(errors, fmt.Sprintf("Error killing process: %s : %v", name, err))
		}
	}

	for name, logfile := range ec.logfiles {
		err := logfile.Close()

		if err != nil {
			errors = append(errors, fmt.Sprintf("Error closing logfile: %s : %v", name, err))
		}
	}

	if len(errors) > 0 {
		return fmt.Errorf("Errors tearing down local exec: %s", strings.Join(errors, ","))
	}

	return nil
}

func createLogFile(name, logdir string) (*os.File, error) {
	if _, err := os.Stat(logdir); os.IsNotExist(err) {
		err := os.MkdirAll(logdir, os.ModePerm)

		if err != nil {
			return nil, fmt.Errorf("Error creating logdir: %v", err)
		}
	}

	outfile, err := os.Create(filepath.Join(logdir, fmt.Sprintf("%s.log", name)))

	if err != nil {
		return nil, fmt.Errorf("Error creating logfile: %v", err)
	}

	return outfile, nil
}

func convertEnvMap(env map[string]string) []string {
	envList := []string{}

	for key, val := range env {
		envList = append(envList, fmt.Sprintf("%s=%s", key, val))
	}

	return envList
}

func (ec *execClient) startTestProcess(name, logdir string, command []string, env map[string]string) error {
	// NOTE: may be useful to check command length here?
	// start command
	cmd := exec.Command(command[0], command[1:]...)

	// pipe logs to file
	outfile, err := createLogFile(name, logdir)

	if err != nil {
		return err
	}

	cmd.Stdout = outfile
	cmd.Env = convertEnvMap(env)
	// NOTE: maybe set parent process ID to test for scenario, scenario for users
	// cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}

	err = cmd.Start()

	if err != nil {
		return fmt.Errorf("Error starting test process: %v", err)
	}

	logrus.Debug("started process: ", name, " : ", cmd.Process.Pid)

	// save process in map
	ec.processes[name] = cmd
	ec.logfiles[name] = outfile

	return nil
}

func (ec *execClient) stopTestProcess(name string) error {
	logrus.Debug("stopping process for ", name)

	// stop process
	cmd, hasCmd := ec.processes[name]

	if !hasCmd {
		return fmt.Errorf("Command not found: %s", name)
	}

	err := cmd.Process.Kill()

	if err != nil {
		return fmt.Errorf("Error killing process: %v", err)
	}

	delete(ec.processes, name)

	// close writer
	file, hasFile := ec.logfiles[name]

	if !hasFile {
		return fmt.Errorf("Log file not found: %s", name)
	}

	err = file.Close()

	if err != nil {
		return fmt.Errorf("Error closing logfile: %v", err)
	}

	delete(ec.logfiles, name)

	return nil
}
