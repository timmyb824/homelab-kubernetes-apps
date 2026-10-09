# Argo Rollouts

**Documentation:** https://argo-rollouts.readthedocs.io/en/stable/installation/#upgrading-argo-rollouts

## Apply CRDs

```bash
kubectl apply --server-side -k https://github.com/argoproj/argo-rollouts/manifests/crds\?ref\=stable
```

## First time install

```bash
kubectl create namespace argo-rollouts
```

## Install

```bash
kubectl apply --server-side -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

## Upgrade

Argo Rollouts is a Kubernetes controller that doesn't hold any external state. It is active only when deployments are actually happening.

To upgrade Argo Rollouts:

- Try to find a time period when no deployments are happening
- Delete the previous version of the controller and apply/install the new one

```bash
kubectl delete --server-side -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply --server-side -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

- When a new Rollout takes place the new controller will be activated.

If deployments are happening while you upgrade the controller, then you shouldn't have any downtime. Current Rollouts will be paused and as soon as the new controller becomes active it will resume all in-flight deployments.
