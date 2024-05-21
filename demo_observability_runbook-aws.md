# Demo Runbook
## Stage 1.<span style="color:Green"> Setting up AWS ENV </span> ✨

Setting up **Git Repo** Environment

```shell
# Init boot strap server and install following
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Setting up Kubectl
curl -O https://s3.us-west-2.amazonaws.com/amazon-eks/1.26.4/2023-05-11/bin/linux/amd64/kubectl
chmod +X kubectl
sudo mv kubectl /usr/local/bin/

# Setting up eksctl

curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
eksctl version


curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 > get_helm.sh
chmod 700 get_helm.sh
./get_helm.sh
helm version


sudo yum install git -y
git clone https://github.com/ray-project/kuberay.git

```

Create an IAM Role with `AdministratorAccess` and attach it to this EC2 instance




## Stage 2. <span style="color:Green"> Creating EKS cluster with cloud formation </span> ⛵

1. Setting up *cluster* 
```shell
eksctl create cluster --name ray-observe-cluster  --region us-east-1 --node-type m5.xlarge
```

## Stage 3.  <span style="color:Green"> Setting up Ray Environment </span> ☀️

2. Enabling kuberay operator
```shell
helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm repo update
kubectl create namespace ray-observability
kubectl config set-context --current --namespace=ray-observability
#Installing kuberay operator
helm install kuberay-operator kuberay/helm-chart/kuberay-operator --version 1.0.0

kubectl get po
#NAME                               READY   STATUS    RESTARTS   AGE
#kuberay-operator-cc5475d57-xpxfd   1/1     Running   0          19s

```

3. Starting Ray Serve
```shell
#copying file from local 
#cd ray-obs/cloud-observability/serve
#scp -i eks-keytab.pem /Users/npatodi/code/observability/serve/ray-serve-observe-exp-aws.yaml ec2-user@ec2-100-27-210-137.compute-1.amazonaws.com:/home/ec2-user/ray

# Now login to server
#ssh -i eks-keytab.pem ec2-user@ec2-100-27-210-137.compute-1.amazonaws.com
kubectl apply -f ray-serve-observe-exp-aws.yaml
kubectl get po
```
Output will be:
```jsunicoderegexp
NAME                                                   READY   STATUS    RESTARTS   AGE
kuberay-operator-8b9dc7c9b-rc4sx                       1/1     Running   0          18m
rs-obs-exp-raycluster-nnlkg-head-9vjwz                 1/1     Running   0          2m20s
rs-obs-exp-raycluster-nnlkg-worker-small-group-mfczw   0/1     Running   0          2m20s
```

## Stage 4.  <span style="color:Green"> Setting up Ray Observability </span> ☀️
Check for service availability
```shell
k get svc
```
Output will be:
```jsunicoderegexp
kuberay-operator                       ClusterIP   10.100.172.58    <none>        8080/TCP                                                            17m
rs-obs-exp-head-svc                    ClusterIP   10.100.226.102   <none>        44217/TCP,10001/TCP,44227/TCP,8265/TCP,6379/TCP,8080/TCP,8000/TCP   90s
rs-obs-exp-raycluster-nnlkg-head-svc   ClusterIP   10.100.160.205   <none>        44217/TCP,10001/TCP,44227/TCP,8265/TCP,6379/TCP,8080/TCP,8000/TCP   112s
rs-obs-exp-serve-svc                   ClusterIP   10.100.170.76    <none>        8000/TCP                                                            90s
```
Port forward headnode and metric server
```shell
# Enable Prom UI
nohup kubectl port-forward --address 0.0.0.0 svc/rs-obs-exp-head-svc 8265:8265 >dashboard.log&

nohup kubectl port-forward --address 0.0.0.0 svc/rs-obs-exp-serve-svc 8000:8000 > rayserve.log&
```


## Stage 5. Cleanup

```shell
eksctl delete cluster --name ray-observe-cluster  --region us-east-1
```