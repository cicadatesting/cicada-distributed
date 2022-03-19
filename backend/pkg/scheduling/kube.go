package scheduling

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	batchV1 "k8s.io/api/batch/v1"
	coreV1 "k8s.io/api/core/v1"
	metaV1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
)

type KubeScheduler struct {
	client iKubeClient
}

type KubeSchedulingMetadata struct {
	Image     string `json:"image"`
	Namespace string `json:"namespace"`
}

func NewKubeScheduler(clientSet *kubernetes.Clientset) *KubeScheduler {
	client := kubeClient{clientSet: clientSet}

	return &KubeScheduler{client: &client}
}

func (s *KubeScheduler) CreateTest(
	testID, backendAddress, schedulingMetadata string,
	tags []string,
	env map[string]string,
) error {
	// load scheduling metadata
	kubeSchedulingMetadata := KubeSchedulingMetadata{}

	err := json.Unmarshal([]byte(schedulingMetadata), &kubeSchedulingMetadata)

	if err != nil {
		return fmt.Errorf("Error loading scheduling metadata: %v", err)
	}

	tagArg := GetTagArg(tags)

	// start test container
	_, err = s.client.createJob(
		kubeSchedulingMetadata.Namespace,
		testID,
		kubeSchedulingMetadata.Image,
		append([]string{
			"run-test",
			"--test-id",
			testID,
			"--backend-address",
			backendAddress,
		}, tagArg...),
		env,
		map[string]string{"type": "cicada-distributed-test", "test": testID},
	)

	if err != nil {
		return fmt.Errorf("Error starting test kube pod: %v", err)
	}

	return nil
}

func (s *KubeScheduler) CreateScenario(
	testID,
	scenarioID,
	scenarioName,
	backendAddress,
	schedulingMetadata,
	encodedContext string,
	env map[string]string,
) error {
	// load scheduling metadata
	kubeSchedulingMetadata := KubeSchedulingMetadata{}

	err := json.Unmarshal([]byte(schedulingMetadata), &kubeSchedulingMetadata)

	if err != nil {
		return fmt.Errorf("Error loading scheduling metadata: %v", err)
	}

	// start scenario container
	_, err = s.client.createJob(
		kubeSchedulingMetadata.Namespace,
		scenarioID,
		kubeSchedulingMetadata.Image,
		[]string{
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
		env,
		map[string]string{
			"type":     "cicada-distributed-scenario",
			"test":     testID,
			"scenario": scenarioName,
		},
	)

	if err != nil {
		return fmt.Errorf("Error starting scenario docker container: %v", err)
	}

	return nil
}

func (s *KubeScheduler) CreateUserManagers(
	userManagerIDs []string,
	testID, scenarioName, backendAddress, schedulingMetadata, encodedContext string,
	env map[string]string,
) error {
	// load scheduling metadata
	kubeSchedulingMetadata := KubeSchedulingMetadata{}

	err := json.Unmarshal([]byte(schedulingMetadata), &kubeSchedulingMetadata)

	if err != nil {
		return fmt.Errorf("Error loading scheduling metadata: %v", err)
	}

	for _, userManagerID := range userManagerIDs {
		_, err := s.client.createJob(
			kubeSchedulingMetadata.Namespace,
			userManagerID,
			kubeSchedulingMetadata.Image,
			[]string{
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
			env,
			map[string]string{
				"type":     "cicada-distributed-user",
				"test":     testID,
				"scenario": scenarioName,
			},
		)

		if err != nil {
			return fmt.Errorf("Error starting user manager docker container: %v", err)
		}
	}

	return nil
}

func (s *KubeScheduler) StopUserManagers(userManagerIDs []string, schedulingMetadata string) error {
	// load scheduling metadata
	kubeSchedulingMetadata := KubeSchedulingMetadata{}

	err := json.Unmarshal([]byte(schedulingMetadata), &kubeSchedulingMetadata)

	if err != nil {
		return fmt.Errorf("Error loading scheduling metadata: %v", err)
	}

	for _, userManagerID := range userManagerIDs {
		err := s.client.stopJob(kubeSchedulingMetadata.Namespace, userManagerID)

		if err != nil {
			return fmt.Errorf("Error stopping user manager: %v", err)
		}
	}

	return nil
}

func (s *KubeScheduler) CleanTestInstances(testID, schedulingMetadata string) error {
	// load scheduling metadata
	kubeSchedulingMetadata := KubeSchedulingMetadata{}

	err := json.Unmarshal([]byte(schedulingMetadata), &kubeSchedulingMetadata)

	if err != nil {
		return fmt.Errorf("Error loading scheduling metadata: %v", err)
	}

	err = s.client.stopJobs(kubeSchedulingMetadata.Namespace, map[string]string{"test": testID})

	if err != nil {
		return fmt.Errorf("Error stopping test instances: %v", err)
	}

	return nil
}

func (s *KubeScheduler) CheckTestInstance(instanceID string, schedulingMetadata string) (bool, error) {
	kubeSchedulingMetadata := KubeSchedulingMetadata{}

	err := json.Unmarshal([]byte(schedulingMetadata), &kubeSchedulingMetadata)

	if err != nil {
		return false, fmt.Errorf("Error loading scheduling metadata: %v", err)
	}

	return s.client.jobIsRunning(kubeSchedulingMetadata.Namespace, instanceID), nil
}

func convertEnv(env map[string]string) []coreV1.EnvVar {
	envVars := []coreV1.EnvVar{}

	for key, value := range env {
		envVars = append(envVars, coreV1.EnvVar{Name: key, Value: value})
	}

	return envVars
}

type iKubeClient interface {
	createJob(
		namespace string,
		name string,
		image string,
		command []string,
		env map[string]string,
		labels map[string]string,
	) (*batchV1.Job, error)
	stopJob(namespace string, name string) error
	stopJobs(namespace string, labels map[string]string) error
	jobIsRunning(namespace, name string) bool
}

type kubeClient struct {
	clientSet *kubernetes.Clientset
}

func (k *kubeClient) createJob(
	namespace string,
	name string,
	image string,
	command []string,
	env map[string]string,
	labels map[string]string,
) (*batchV1.Job, error) {
	// create job to run scenario in
	batchV1Client := k.clientSet.BatchV1()
	ctx := context.Background()

	job := batchV1.Job{
		ObjectMeta: metaV1.ObjectMeta{
			Name: name,
		},
		Spec: batchV1.JobSpec{
			Parallelism:  func() *int32 { i := int32(1); return &i }(),
			Completions:  func() *int32 { i := int32(1); return &i }(),
			BackoffLimit: func() *int32 { i := int32(0); return &i }(),
			Template: coreV1.PodTemplateSpec{
				ObjectMeta: metaV1.ObjectMeta{
					Labels: labels,
				},
				// FEATURE: resource limits (additional args decorator)
				Spec: coreV1.PodSpec{
					RestartPolicy:      coreV1.RestartPolicyNever,
					ServiceAccountName: "cicada-distributed-job",
					Containers: []coreV1.Container{
						{
							Name:  "container",
							Image: image,
							Args:  command,
							Env:   convertEnv(env),
						},
					},
				},
			},
		},
	}

	return batchV1Client.Jobs(namespace).Create(ctx, &job, metaV1.CreateOptions{})
}

func (k *kubeClient) stopJob(namespace string, name string) error {
	batchV1Client := k.clientSet.BatchV1()
	ctx := context.Background()
	propogationPolicy := metaV1.DeletePropagationBackground

	return batchV1Client.Jobs(namespace).Delete(ctx, name, metaV1.DeleteOptions{
		PropagationPolicy: &propogationPolicy,
	})
}

func (k *kubeClient) stopJobs(namespace string, labels map[string]string) error {
	batchV1Client := k.clientSet.BatchV1()
	ctx := context.Background()
	propogationPolicy := metaV1.DeletePropagationBackground

	labelSelector := []string{}

	for key, value := range labels {
		labelSelector = append(labelSelector, fmt.Sprintf("%s=%s", key, value))
	}

	return batchV1Client.Jobs(namespace).DeleteCollection(
		ctx,
		metaV1.DeleteOptions{
			PropagationPolicy: &propogationPolicy,
		},
		metaV1.ListOptions{
			LabelSelector: strings.Join(labelSelector, ","),
		},
	)
}

func (k *kubeClient) jobIsRunning(namespace, name string) bool {
	batchV1Client := k.clientSet.BatchV1()
	ctx := context.Background()

	job, err := batchV1Client.Jobs(namespace).Get(ctx, name, metaV1.GetOptions{})

	if err != nil {
		return false
	}

	return job.Status.Active > 0
}

// func (k *kubeClient) getScale(namespace, name string) (*autoscalingV1.Scale, error) {
// 	appsV1Client := k.clientSet.AppsV1()
// 	ctx := context.Background()

// 	return appsV1Client.Deployments(namespace).GetScale(ctx, name, metaV1.GetOptions{})
// }

// func (k *kubeClient) updateScale(namespace, name string, scale *autoscalingV1.Scale, count int32) (*autoscalingV1.Scale, error) {
// 	appsV1Client := k.clientSet.AppsV1()
// 	ctx := context.Background()

// 	scale.Spec.Replicas = count

// 	return appsV1Client.Deployments(namespace).UpdateScale(
// 		ctx,
// 		name,
// 		scale,
// 		metaV1.UpdateOptions{},
// 	)
// }

// func (k *kubeClient) createDeployment(
// 	namespace, name, image string,
// 	users *int32,
// 	command []string,
// 	env, labels map[string]string,
// ) (*appsV1.Deployment, error) {
// 	appsV1Client := k.clientSet.AppsV1()
// 	ctx := context.Background()

// 	deploymentSpec := &appsV1.Deployment{
// 		ObjectMeta: metaV1.ObjectMeta{
// 			Name: name,
// 		},
// 		Spec: appsV1.DeploymentSpec{
// 			Replicas: users,
// 			Selector: &metaV1.LabelSelector{
// 				MatchLabels: labels,
// 			},
// 			Template: coreV1.PodTemplateSpec{
// 				ObjectMeta: metaV1.ObjectMeta{
// 					Labels: labels,
// 				},
// 				Spec: coreV1.PodSpec{
// 					Containers: []coreV1.Container{
// 						{
// 							Name:    "container",
// 							Image:   image,
// 							Command: command,
// 							Env:     convertEnv(env),
// 						},
// 					},
// 				},
// 			},
// 		},
// 	}

// 	return appsV1Client.Deployments(namespace).Create(ctx, deploymentSpec, metaV1.CreateOptions{})
// }

// func (k *kubeClient) deleteDeployment(namespace, name string) error {
// 	appsV1Client := k.clientSet.AppsV1()
// 	ctx := context.Background()

// 	return appsV1Client.Deployments(namespace).Delete(ctx, name, metaV1.DeleteOptions{})
// }
