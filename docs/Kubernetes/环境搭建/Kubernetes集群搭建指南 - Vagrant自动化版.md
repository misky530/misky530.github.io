# Kubernetes集群搭建指南 - Vagrant自动化版

## 阶段一：安装必要软件

### 1.1 安装VirtualBox

#### 下载安装

1. 访问：https://www.virtualbox.org/wiki/Downloads
2. 下载 **Windows hosts** 版本（7.0.x）
3. 下载 **VirtualBox Extension Pack**
4. 双击安装，默认选项即可
5. 安装Extension Pack（管理 → 全局设定 → 扩展）

------

### 1.2 安装Vagrant

#### 下载安装

1. 访问：https://www.vagrantup.com/downloads
2. 下载 **Windows 64-bit** 版本
3. 双击 `vagrant_x.x.x_windows_amd64.msi` 安装
4. 默认选项一路下一步
5. **重启电脑**（重要！使环境变量生效）

#### 验证安装

重启后，打开PowerShell或CMD：

powershell

```powershell
vagrant --version
```

应该显示类似：`Vagrant 2.4.0`

------

### 1.3 安装Git（可选但推荐）

用于下载Kubespray项目。

1. 访问：https://git-scm.com/download/win
2. 下载并安装
3. 验证：

powershell

```powershell
git --version
```

------

## 阶段二：准备工作目录

### 2.1 创建项目目录

在PowerShell中执行：

powershell

```powershell
# 创建工作目录
mkdir D:\k8s-cluster
cd D:\k8s-cluster

# 创建子目录
mkdir vagrant
mkdir kubespray
```

------

## 阶段三：创建Vagrantfile

### 3.1 编写Vagrantfile

在 `D:\k8s-cluster\vagrant` 目录创建文件 `Vagrantfile`（无扩展名）

使用记事本或VS Code创建，内容如下：

ruby

```ruby
# -*- mode: ruby -*-
# vi: set ft=ruby :

# 集群配置
CONTROL_COUNT = 3
WORKER_COUNT = 3
BOX_IMAGE = "ubuntu/jammy64"  # Ubuntu 22.04
NETWORK_PREFIX = "192.168.56"

Vagrant.configure("2") do |config|
  config.vm.box = BOX_IMAGE
  config.vm.box_check_update = false

  # 控制节点
  (1..CONTROL_COUNT).each do |i|
    config.vm.define "k8s-control-#{i}" do |node|
      node.vm.hostname = "k8s-control-#{i}"
      node.vm.network "private_network", ip: "#{NETWORK_PREFIX}.#{10+i}"
      
      node.vm.provider "virtualbox" do |vb|
        vb.name = "k8s-control-#{i}"
        vb.memory = "2048"
        vb.cpus = 2
        vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
      end
    end
  end

  # 工作节点
  (1..WORKER_COUNT).each do |i|
    config.vm.define "k8s-worker-#{i}" do |node|
      node.vm.hostname = "k8s-worker-#{i}"
      node.vm.network "private_network", ip: "#{NETWORK_PREFIX}.#{20+i}"
      
      node.vm.provider "virtualbox" do |vb|
        vb.name = "k8s-worker-#{i}"
        vb.memory = "4096"
        vb.cpus = 2
        vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
      end
    end
  end

  # 基础配置脚本（所有节点执行）
  config.vm.provision "shell", inline: <<-SHELL
    # 更新系统
    apt-get update
    
    # 安装必要软件
    apt-get install -y curl wget vim net-tools
    
    # 配置SSH
    sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
    systemctl restart sshd
    
    # 设置vagrant用户密码（用于ansible连接）
    echo "vagrant:vagrant" | chpasswd
    
    # 禁用swap（K8s要求）
    swapoff -a
    sed -i '/swap/d' /etc/fstab
    
    # 配置内核参数
    cat <<EOF | tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
    
    modprobe overlay
    modprobe br_netfilter
    
    cat <<EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
    
    sysctl --system
    
    echo "Node $(hostname) provisioned successfully!"
  SHELL
end
```

### 3.2 IP地址分配表

Vagrant会自动分配以下IP：

```
主机名IP地址角色内存CPU
k8s-control-1192.168.56.11Control Plane2GB2
k8s-control-2192.168.56.12Control Plane2GB2
k8s-control-3192.168.56.13Control Plane2GB2
k8s-worker-1192.168.56.21Worker4GB2
k8s-worker-2192.168.56.22Worker4GB2
k8s-worker-3192.168.56.23Worker4GB2
```

------

## 阶段四：启动虚拟机

### 4.1 下载Box镜像

第一次运行会自动下载Ubuntu镜像（约600MB）：

powershell

```powershell
cd D:\k8s-cluster\vagrant
vagrant box add ubuntu/jammy64
```

或者直接启动（会自动下载）：

powershell

```powershell
vagrant up
```

### 4.2 启动所有虚拟机

powershell

```powershell
cd D:\k8s-cluster\vagrant

# 启动所有虚拟机（大约10-15分钟）
vagrant up
```

**过程说明**：

- 自动创建6台虚拟机
- 自动配置网络
- 自动执行初始化脚本
- 自动配置SSH

### 4.3 验证虚拟机状态

powershell

```powershell
# 查看所有虚拟机状态
vagrant status

# 应该看到：
# k8s-control-1    running (virtualbox)
# k8s-control-2    running (virtualbox)
# k8s-control-3    running (virtualbox)
# k8s-worker-1     running (virtualbox)
# k8s-worker-2     running (virtualbox)
# k8s-worker-3     running (virtualbox)
```

### 4.4 测试SSH连接

powershell

```powershell
# 连接到control-1
vagrant ssh k8s-control-1

# 在虚拟机内测试网络
ping -c 2 192.168.56.12
ping -c 2 192.168.56.21

# 退出
exit
```

------

## 阶段五：常用Vagrant命令

### 虚拟机管理

powershell

```powershell
# 启动所有虚拟机
vagrant up

# 启动单个虚拟机
vagrant up k8s-control-1

# 关闭所有虚拟机
vagrant halt

# 重启所有虚拟机
vagrant reload

# 删除所有虚拟机（重新开始）
vagrant destroy -f

# 查看状态
vagrant status

# 查看全局状态
vagrant global-status
```

### SSH连接

powershell

```powershell
# SSH到指定虚拟机
vagrant ssh k8s-control-1
vagrant ssh k8s-worker-1

# 获取SSH配置信息
vagrant ssh-config k8s-control-1
```

------

## 故障排查

### 问题1：启动慢或卡住

**解决**：

powershell

```powershell
# 单独启动每台机器
vagrant up k8s-control-1
vagrant up k8s-control-2
# ... 依次启动
```

### 问题2：网络无法连通

**检查**：

powershell

```powershell
# 在宿主机ping虚拟机
ping 192.168.56.11

# 如果不通，检查VirtualBox网络
# VirtualBox → 文件 → 主机网络管理器
# 确保有 192.168.56.1/24 网络
```

### 问题3：虚拟化未启用

**错误信息**：`VT-x is disabled`

**解决**：

1. 重启电脑进入BIOS
2. 启用Intel VT-x或AMD-V
3. 保存退出

------

## 下一步准备

完成后确认：

-  VirtualBox已安装
-  Vagrant已安装并验证版本
-  Vagrantfile已创建
-  `vagrant up` 成功启动所有虚拟机
-  可以SSH连接到虚拟机
-  虚拟机之间网络互通

完成后告诉我，我们进入下一阶段：**安装WSL2和Ansible**