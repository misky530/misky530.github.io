# WSL2和Ansible安装指南

## 阶段三：安装WSL2

### 3.1 检查Windows版本

WSL2需要：
- Windows 10 版本 1903 或更高（内部版本 18362 或更高）
- Windows 11 任意版本

**检查版本**：
```powershell
# 在PowerShell中运行
winver
```

### 3.2 安装WSL2（简化命令）

在PowerShell（管理员模式）中运行：

```powershell
# 一键安装WSL2和Ubuntu
wsl --install

# 如果已经安装过WSL1，升级到WSL2
wsl --set-default-version 2
```

**这个命令会自动**：
- 启用WSL功能
- 启用虚拟机平台
- 下载Linux内核更新
- 安装Ubuntu（默认发行版）

### 3.3 重启电脑

安装完成后**必须重启电脑**。

---

## 阶段四：配置Ubuntu和安装Ansible

### 4.1 启动WSL

重启后，有两种方式启动WSL：

**方法一**：在开始菜单搜索并打开 **Ubuntu**

**方法二**：在PowerShell中运行：
```powershell
wsl
```

### 4.2 首次配置Ubuntu

首次启动会要求创建用户：
```bash
# 输入用户名（建议：你的英文名小写）
Enter new UNIX username: yourname

# 输入密码（输入时不显示，正常）
New password: 
Retype new password:
```

### 4.3 更新Ubuntu系统

在WSL Ubuntu中运行：
```bash
# 更新软件包列表
sudo apt update

# 升级已安装的软件包
sudo apt upgrade -y
```

### 4.4 安装Ansible

```bash
# 安装必要的依赖
sudo apt install -y python3 python3-pip git

# 安装Ansible
sudo apt install -y ansible

# 验证安装
ansible --version
```

应该看到类似输出：
```
ansible [core 2.12.x]
  python version = 3.10.x
```

### 4.5 安装额外的Python依赖

Kubespray需要一些额外的Python库：
```bash
# 安装依赖
sudo apt install -y python3-jinja2 python3-netaddr python3-yaml
pip3 install jinja2 netaddr
```

---

## 阶段五：配置SSH访问虚拟机

### 5.1 测试从WSL访问虚拟机

在WSL中测试网络连通性：
```bash
# 测试ping
ping -c 2 192.168.56.11

# 测试SSH（密码：vagrant）
ssh vagrant@192.168.56.11
```

**如果ping不通**，需要配置Windows防火墙或WSL网络。

### 5.2 生成SSH密钥（推荐）

在WSL中生成SSH密钥对：
```bash
# 生成密钥
ssh-keygen -t rsa -b 4096 -C "k8s-cluster"

# 直接回车使用默认路径
Enter file in which to save the key (/home/yourname/.ssh/id_rsa): [回车]

# 设置密码（可以为空，直接回车）
Enter passphrase (empty for no passphrase): [回车]
Enter same passphrase again: [回车]
```

### 5.3 将SSH公钥复制到所有虚拟机

```bash
# 复制到所有节点（每个节点都要执行，密码是vagrant）
ssh-copy-id vagrant@192.168.56.11
ssh-copy-id vagrant@192.168.56.12
ssh-copy-id vagrant@192.168.56.13
ssh-copy-id vagrant@192.168.56.21
ssh-copy-id vagrant@192.168.56.22
ssh-copy-id vagrant@192.168.56.23

# 每次输入密码：vagrant
```

### 5.4 验证免密登录

```bash
# 测试免密登录（应该不需要密码）
ssh vagrant@192.168.56.11

# 成功后退出
exit
```

---

## 阶段六：下载Kubespray

### 6.1 克隆Kubespray仓库

在WSL中：
```bash
# 进入home目录
cd ~

# 克隆Kubespray
git clone https://github.com/kubernetes-sigs/kubespray.git

# 进入目录
cd kubespray

# 切换到稳定版本（推荐）
git checkout release-2.24

# 查看当前版本
git describe --tags
```

### 6.2 安装Kubespray依赖

```bash
# 确保在kubespray目录
cd ~/kubespray

# 安装Python依赖
pip3 install -r requirements.txt

# 或者使用系统包管理器
sudo apt install -y python3-jinja2 python3-netaddr python3-yaml
```

---

## 完成检查清单

在继续之前，确认以下都已完成：

- [ ] WSL2已安装并重启
- [ ] Ubuntu已配置（创建了用户）
- [ ] Ansible已安装并验证版本
- [ ] 从WSL能ping通所有虚拟机（192.168.56.11-23）
- [ ] SSH密钥已生成
- [ ] 所有虚拟机已配置免密登录
- [ ] Kubespray已下载

---

## 下一步

完成后告诉我，我们将进入：**配置Kubespray inventory并部署K8s集群**！
