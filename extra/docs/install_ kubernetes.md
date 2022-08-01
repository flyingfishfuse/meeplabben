
# How to install kubernetes on Debian
Update the apt package index and install packages needed to use the Kubernetes apt repository:

    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl

Download the Google Cloud public signing key:

    sudo curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg

Add the Kubernetes apt repository:

    echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list

Update apt package index, install kubelet, kubeadm and kubectl, and pin their version:
    
    sudo apt-get update
    sudo apt-get install -y kubelet kubeadm kubectl
    sudo apt-mark hold kubelet kubeadm kubectl



# how to configure the kubelet cgroup driver to match the container
runtime cgroup driver for kubeadm clusters.

## prerequisites

You should be familiar with the Kubernetes
[container runtime requirements](/docs/setup/production-environment/container-runtimes).

<!-- steps -->

## Configuring the container runtime cgroup driver

The [Container runtimes](/docs/setup/production-environment/container-runtimes) page
explains that the `systemd` driver is recommended for kubeadm based setups instead
of the `cgroupfs` driver, because kubeadm manages the kubelet as a systemd service.

The page also provides details on how to setup a number of different container runtimes with the
`systemd` driver by default.

## Configuring the kubelet cgroup driver

kubeadm allows you to pass a `KubeletConfiguration` structure during `kubeadm init`.
This `KubeletConfiguration` can include the `cgroupDriver` field which controls the cgroup
driver of the kubelet.


In v1.22, if the user is not setting the `cgroupDriver` field under `KubeletConfiguration`,
`kubeadm` will default it to `systemd`.
{{< /note >}}

A minimal example of configuring the field explicitly:

```yaml
# kubeadm-config.yaml
kind: ClusterConfiguration
apiVersion: kubeadm.k8s.io/v1beta3
kubernetesVersion: v1.21.0
---
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
cgroupDriver: systemd
```

Such a configuration file can then be passed to the kubeadm command:

```shell
kubeadm init --config kubeadm-config.yaml
```

{{< note >}}
Kubeadm uses the same `KubeletConfiguration` for all nodes in the cluster.
The `KubeletConfiguration` is stored in a [ConfigMap](/docs/concepts/configuration/configmap)
object under the `kube-system` namespace.

Executing the sub commands `init`, `join` and `upgrade` would result in kubeadm
writing the `KubeletConfiguration` as a file under `/var/lib/kubelet/config.yaml`
and passing it to the local node kubelet.
{{< /note >}}

## Using the `cgroupfs` driver

To use `cgroupfs` and to prevent `kubeadm upgrade` from modifying the
`KubeletConfiguration` cgroup driver on existing setups, you must be explicit
about its value. This applies to a case where you do not wish future versions
of kubeadm to apply the `systemd` driver by default.

See the below section on "[Modify the kubelet ConfigMap](#modify-the-kubelet-configmap)" for details on
how to be explicit about the value.

If you wish to configure a container runtime to use the `cgroupfs` driver,
you must refer to the documentation of the container runtime of your choice.

## Migrating to the `systemd` driver

To change the cgroup driver of an existing kubeadm cluster to `systemd` in-place,
a similar procedure to a kubelet upgrade is required. This must include both
steps outlined below.

{{< note >}}
Alternatively, it is possible to replace the old nodes in the cluster with new ones
that use the `systemd` driver. This requires executing only the first step below
before joining the new nodes and ensuring the workloads can safely move to the new
nodes before deleting the old nodes.
{{< /note >}}

### Modify the kubelet ConfigMap

- Call `kubectl edit cm kubelet-config -n kube-system`.
- Either modify the existing `cgroupDriver` value or add a new field that looks like this:

  ```yaml
  cgroupDriver: systemd
  ```
  This field must be present under the `kubelet:` section of the ConfigMap.

### Update the cgroup driver on all nodes

For each node in the cluster:

- [Drain the node](/docs/tasks/administer-cluster/safely-drain-node) using `kubectl drain <node-name> --ignore-daemonsets`
- Stop the kubelet using `systemctl stop kubelet`
- Stop the container runtime
- Modify the container runtime cgroup driver to `systemd`
- Set `cgroupDriver: systemd` in `/var/lib/kubelet/config.yaml`
- Start the container runtime
- Start the kubelet using `systemctl start kubelet`
- [Uncordon the node](/docs/tasks/administer-cluster/safely-drain-node) using `kubectl uncordon <node-name>`

Execute these steps on nodes one at a time to ensure workloads
have sufficient time to schedule on different nodes.

Once the process is complete ensure that all nodes and workloads are healthy.