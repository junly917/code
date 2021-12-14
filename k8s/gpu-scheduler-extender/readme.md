# GPU共享调度方案

## 概述

基于 Nvidia GPU 的推理等一些相关的任务可以在同一个 Nvidia GPU 设备上运行，以提高 GPU 利用率。一个Kubernetes Pods可以在一台机器的某张卡进行任务运行，能做到简单的隔离功能，

此教程参考：阿里云容器服务开源文档  `https://github.com/AliyunContainerService/gpushare-scheduler-extender`

## 部署的先决条件

- Kubernetes 1.11 至1.22(含)

- NVIDIA 驱动程序 ~= 361.93

- Nvidia-docker 版本 > 2.0

## 安装指南

1. 准备Docker运行时环境

   `vim /etc/docker/daemon.json`

   ```shell
   {
       "default-runtime": "nvidia",
       "runtimes": {
           "nvidia": {
               "path": "/usr/bin/nvidia-container-runtime",
               "runtimeArgs": []
           }
       }
   }
   ```

2. 准备好相关的镜像

   ```shell
   # ls -l
   app.yaml               
   device-plugin-rbac.yaml  
   gpushare-schd-extender.yaml   
   kubectl-inspect-gpushare.zip  
   readme.md 	
   device-plugin-ds.yaml  
   gpushare-device-plugin/  
   gpushare-scheduler-extender/  
   kube-scheduler.yaml           
   scheduler-policy-config.json
   
   # cd gpushare-device-plugin 
   # docker build -t gpushare-device-plugin:v1.0  .
   # cd gpushare-scheduler-extender
   # docker build -t gpushare-scheduler-extender:v1.0  .
   ```

3. 部署调度控制器Control

   ```shell
   # curl -O https://raw.githubusercontent.com/AliyunContainerService/gpushare-scheduler-extender/master/config/gpushare-schd-extender.yaml
   # kubectl create -f gpushare-schd-extender.yaml  # 使用目录中的文件， 镜像需要修改成手动构建出来的镜像 gpushare-scheduler-extender:v1.0
   # kubectl  get pods -n kube-system 
   NAME                                      READY   STATUS    RESTARTS   AGE
   coredns-7ff77c879f-7qbs8                  1/1     Running   1          16h
   coredns-7ff77c879f-slcwv                  1/1     Running   1          16h
   etcd-dev-server-153                       1/1     Running   1          16h
   gpushare-schd-extender-7f6b8b5b57-c98k5   1/1     Running   4          15h   # 需要显示此pods
   kube-apiserver-dev-server-153             1/1     Running   1          16h
   kube-controller-manager-dev-server-153    1/1     Running   1          16h
   kube-flannel-ds-g5bcj                     1/1     Running   1          16h
   kube-proxy-p5dsw                          1/1     Running   1          16h
   kube-scheduler-dev-server-153             1/1     Running   1          16h
   
   ```

   

4. 修改调度器配置文件

   - 将`scheduler-policy-config.json`配置文件放到kube-schedule节点的指定位置如`/etc/kubernetes/scheduler-policy-config.json`

   - 修改主配置文件

     使用kubeadm 安装的： `/etc/kubernetes/manifests/kube-scheduler.yaml` 

     使用二进制部署的：`/etc/systemd/system/kube-scheduler.service `  

     

     添加调度策略文件

     `- --policy-config-file=/etc/kubernetes/scheduler-policy-config.json`

     \# kubeadm安装 的需要  Add volume mount into Pod Spec ,  \# 如果使用二进制安装的则不需要配置

     ```shell
     - mountPath: /etc/kubernetes/scheduler-policy-config.json
       name: scheduler-policy-config
       readOnly: true
     ```

     ```shell
     - hostPath:
           path: /etc/kubernetes/scheduler-policy-config.json
           type: FileOrCreate
       name: scheduler-policy-config
     ```

     

5. 部署Device的相关插件

   在所有的gpu节点上部署pods

   ```shell
   # kubectl create -f device-plugin-rbac.yaml
   # kubectl create -f device-plugin-ds.yaml   # 需要注意镜像要使用之前我们手动构建的镜像 gpushare-device-plugin
   # kubectl  get pods -n kube-system 
   NAME                                      READY   STATUS    RESTARTS   AGE
   coredns-7ff77c879f-7qbs8                  1/1     Running   1          16h
   coredns-7ff77c879f-slcwv                  1/1     Running   1          16h
   etcd-dev-server-153                       1/1     Running   1          16h
   gpushare-device-plugin-ds-c9ctv           1/1     Running   0          15h  # 需要看到此pod正常运行
   gpushare-schd-extender-7f6b8b5b57-c98k5   1/1     Running   4          15h
   kube-apiserver-dev-server-153             1/1     Running   1          16h
   kube-controller-manager-dev-server-153    1/1     Running   1          16h
   kube-flannel-ds-g5bcj                     1/1     Running   1          16h
   kube-proxy-p5dsw                          1/1     Running   1          16h
   kube-scheduler-dev-server-153             1/1     Running   1          16h
   ```

   

6. 配置GPU节点打上固定标签 并下载inspect-gpushare插件
   对的有的GPU节点设置标签配置

   ```shell
   # kubectl label node <target_node> gpushare=true
   
   # wget https://github.com/AliyunContainerService/gpushare-device-plugin/releases/download/v0.3.0/kubectl-inspect-gpushare  # 也可以使用文件夹内的软件包 kubectl-inspect-gpushare.zip  
   
   # unzip kubectl-inspect-gpushare.zip  
   # chmod u+x /usr/bin/kubectl-inspect-gpushare
   
   # ./kubectl-inspect-gpushare # 查看获取的GPU信息, 机器上有8卡A30显卡,
   NAME            IPADDRESS      GPU0(Allocated/Total)  GPU1(Allocated/Total)  GPU2(Allocated/Total)  GPU3(Allocated/Total)  GPU4(Allocated/Total)  GPU5(Allocated/Total)  GPU6(Allocated/Total)  GPU7(Allocated/Total)  GPU Memory(GiB)
   dev-server-153  192.168.0.153  0/23                   0/23                   0/23                   0/23                   0/23                   0/23                   0/23                   0/23                   0/184
   -----------------------------------------------------------------------------------------------
   Allocated/Total GPU Memory In Cluster:
   0/184 (0%) 
   
   # kubectl inspect gpushare -d  可以获取详细信息
   ```

   

## 创建测试用例

```shell
# cat app.yaml
apiVersion: apps/v1beta1
kind: StatefulSet

metadata:
  name: binpack-1
  labels:
    app: binpack-1

spec:
  replicas: 3
  serviceName: "binpack-1"
  podManagementPolicy: "Parallel"
  selector: # define how the deployment finds the pods it manages
    matchLabels:
      app: binpack-1

  template: # define the pods specifications
    metadata:
      labels:
        app: binpack-1

    spec:
      containers:
      - name: binpack-1
        image: cheyang/gpu-player:v2
        resources:
          limits:
            # GiB  需要指定此pod需要多少的显存, 分配完之后可以使用nvidia-smi查看
            aliyun.com/gpu-mem: 3
```

目前此方案优点：

1. 可以限制单个Pod只运行在一片卡上，如果使用kubernetes默认调度策略，则会所在所有的卡上创建对应的进程，如果使用多卡的时候是否会出现来回调度问题

2. Pods无法申请大于单片卡的最大容量

3. 此方案暂时无法申请多卡进行调度，即pods申请4卡，每张卡3G这种方案

   