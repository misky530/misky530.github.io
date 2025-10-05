又是镜像拉取问题。检查这个Pod在哪个节点：
kubectl get pod mysql-fcf4896c-7s9lv -o wide

worker-3有镜像加速配置，但还是拉取失败。查看具体错误：
kubectl describe pod mysql-fcf4896c-7s9lv | grep -A 20 "Events:"

