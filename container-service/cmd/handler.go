package cmd

import (
	"fmt"

	"github.com/cicadatesting/container-service/api"
	"github.com/cicadatesting/container-service/pkg"
)

type Handler interface {
	StartContainer(*api.StartContainerRequest) error
	StopContainer(*api.StopContainerRequest) error
	StopContainers(*api.StopContainersRequest) error
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
	containerArgs := req.GetDockerContainerArgs()

	if containerArgs == nil {
		return fmt.Errorf("Invalid Docker args")
	}

	if containerArgs.Network != nil {
		network = &containerArgs.Network.Value
	}

	err := h.dockerRunner.StartContainer(
		containerArgs.GetImage(),
		req.GetName(),
		containerArgs.GetCommand(),
		req.GetLabels(),
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
	return h.dockerRunner.StopContainer(req.GetName())
}

func (h *DockerHandler) StopContainers(req *api.StopContainersRequest) error {
	return h.dockerRunner.StopContainers(req.GetLabels())
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
	containerArgs := req.GetKubeContainerArgs()

	if containerArgs == nil {
		return fmt.Errorf("Invalid Kube args")
	}

	return h.kubeRunner.RunJob(
		req.GetNamespace(),
		req.GetName(),
		containerArgs.GetImage(),
		containerArgs.GetCommand(),
		containerArgs.GetEnv(),
		req.GetLabels(),
	)
}

func (h *KubeHandler) StopContainer(req *api.StopContainerRequest) error {
	return h.kubeRunner.CleanJob(req.GetNamespace(), req.GetName())
}

func (h *KubeHandler) StopContainers(req *api.StopContainersRequest) error {
	return h.kubeRunner.CleanJobs(req.GetNamespace(), req.GetLabels())
}

func (h *KubeHandler) ContainerRunning(req *api.DescribeContainerRequest) bool {
	return h.kubeRunner.JobRunning(req.GetNamespace(), req.GetName())
}
