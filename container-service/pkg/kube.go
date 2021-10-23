package pkg

import (
	"context"
	"fmt"
	"strings"

	batchV1 "k8s.io/api/batch/v1"
	coreV1 "k8s.io/api/core/v1"
	metaV1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
)

type KubeRunner struct {
	client iKubeClient
}

func NewKubeRunner(clientSet *kubernetes.Clientset) *KubeRunner {
	client := kubeClient{clientSet: clientSet}

	return &KubeRunner{client: &client}
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

func (r *KubeRunner) RunJob(
	namespace string,
	name string,
	image string,
	command []string,
	env map[string]string,
	labels map[string]string,
) error {
	_, err := r.client.createJob(namespace, name, image, command, env, labels)

	if err != nil {
		return fmt.Errorf("Error creating job: %v", err)
	}

	return nil
}

func (r *KubeRunner) CleanJob(namespace string, name string) error {
	err := r.client.stopJob(namespace, name)

	if err != nil {
		return fmt.Errorf("Error stopping job: %v", err)
	}

	return nil
}

func (r *KubeRunner) CleanJobs(namespace string, labels map[string]string) error {
	err := r.client.stopJobs(namespace, labels)

	if err != nil {
		return fmt.Errorf("Error stopping jobs: %v", err)
	}

	return nil
}

func (r *KubeRunner) JobRunning(namespace, name string) bool {
	return r.client.jobIsRunning(namespace, name)
}

// func (r *KubeRunner) StartUsers(
// 	namespace string,
// 	count int,
// 	image string,
// 	name string,
// 	command []string,
// 	labels map[string]string,
// 	env map[string]string,
// ) error {
// 	// determine if deployment exists for users in scenario
// 	// if no deployment exists, create one. else, scale up scenario
// 	// config, err := rest.InClusterConfig()

// 	// if err != nil {
// 	// 	panic(err)
// 	// }

// 	// clientset, err := kubernetes.NewForConfig(config)

// 	// if err != nil {
// 	// 	panic(err)
// 	// }
// 	scale, err := r.client.getScale(namespace, name)

// 	if err != nil && errors.IsNotFound(err) {
// 		// create deployment if not found
// 		labels["scenario"] = name

// 		_, err := r.client.createDeployment(namespace, name, image, func() *int32 { i := int32(count); return &i }(), command, env, labels)

// 		return err
// 	} else if err != nil {
// 		return err
// 	}

// 	_, err = r.client.updateScale(namespace, name, scale, scale.Spec.Replicas+int32(count))

// 	return err
// }

// func (r *KubeRunner) StopUsers(namespace string, name string, count int) error {
// 	scale, err := r.client.getScale(namespace, name)

// 	if err != nil {
// 		return err
// 	}

// 	if count >= int(scale.Spec.Replicas) {
// 		// if removing all users, delete deployment
// 		return r.client.deleteDeployment(namespace, name)
// 	}

// 	// scale down users
// 	_, err = r.client.updateScale(namespace, name, scale, scale.Spec.Replicas-int32(count))

// 	return err
// }

// func (r *KubeRunner) CleanUsers(namespace, name string) error {
// 	// delete deployment for users in scenario
// 	return r.client.deleteDeployment(namespace, name)
// }
