package cmd

import (
	"fmt"

	"github.com/cicadatesting/container-service/api"
	"github.com/cicadatesting/container-service/pkg"
)

type Handler interface {
	StartContainer(*api.StartContainerRequest) error
	StopContainer(*api.StopContainerRequest) error
	ContainerRunning(*api.DescribeContainerRequest) bool
}

type DockerHandler struct {
	dockerRunner *pkg.DockerRunner
}

func NewDockerHandler(runner *pkg.DockerRunner) *DockerHandler {
	return &DockerHandler{dockerRunner: runner}
}

func (h *DockerHandler) StartContainer(req *api.StartContainerRequest) error {
	// var hostPort *int
	// var containerPort *int
	var network *string
	// var createNetwork *bool

	// if req.HostPort != nil {
	// 	hp := int(req.HostPort.Value)

	// 	hostPort = &hp
	// }

	// if req.ContainerPort != nil {
	// 	cp := int(req.ContainerPort.Value)

	// 	containerPort = &cp
	// }

	// if req.CreateNetwork != nil {
	// 	createNetwork = &req.CreateNetwork.Value
	// }

	// volumes := []pkg.DockerVolume{}

	// for _, volume := range req.GetVolumes() {
	// 	volumes = append(volumes, pkg.DockerVolume{Source: volume.Source, Destination: volume.Destination})
	// }

	args := req.GetDockerArgs()
	containerArgs := req.GetDockerContainerArgs()

	if args == nil || containerArgs == nil {
		return fmt.Errorf("Invalid Docker args")
	}

	if containerArgs.Network != nil {
		network = &containerArgs.Network.Value
	}

	err := h.dockerRunner.StartContainer(
		containerArgs.GetImage(),
		req.GetName(),
		containerArgs.GetCommand(),
		args.GetLabels(),
		containerArgs.GetEnv(),
		// volumes,
		// hostPort,
		// containerPort,
		network,
		// createNetwork,
	)

	if err != nil {
		return err
	}

	return nil
}

func (h *DockerHandler) StopContainer(req *api.StopContainerRequest) error {
	args := req.GetDockerArgs()

	if args == nil {
		return fmt.Errorf("Invalid Docker args")
	}

	return h.dockerRunner.StopContainer(req.GetName(), args.GetLabels())
}

func (h *DockerHandler) ContainerRunning(req *api.DescribeContainerRequest) bool {
	return h.dockerRunner.ContainerIsRunning(req.GetName())
}

type KubeHandler struct {
	kubeRunner *pkg.KubeRunner
}

func NewKubeHandler(runner *pkg.KubeRunner) *KubeHandler {
	return &KubeHandler{kubeRunner: runner}
}

func (h *KubeHandler) StartContainer(req *api.StartContainerRequest) error {
	args := req.GetKubeArgs()
	containerArgs := req.GetKubeContainerArgs()

	if args == nil || containerArgs == nil {
		return fmt.Errorf("Invalid Kube args")
	}

	return h.kubeRunner.RunJob(
		args.GetNamespace(),
		req.GetName(),
		containerArgs.GetImage(),
		containerArgs.GetCommand(),
		containerArgs.GetEnv(),
		args.GetLabels(),
	)
}

func (h *KubeHandler) StopContainer(req *api.StopContainerRequest) error {
	args := req.GetKubeArgs()

	if args == nil {
		return fmt.Errorf("Invalid Kube args")
	}

	return h.kubeRunner.CleanJobs(args.GetNamespace(), req.GetName(), args.GetLabels())
}

func (h *KubeHandler) ContainerRunning(req *api.DescribeContainerRequest) bool {
	return h.kubeRunner.JobRunning(req.GetNamespace(), req.GetName())
}
