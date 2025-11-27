terraform {
  required_providers {
    linode = {
      source  = "linode/linode"
      version = "~> 2.0"
    }
  }
}

provider "linode" {
  token = var.linode_token
}

resource "linode_firewall" "dev_fw" {
  label           = "dev-firewall"
  inbound_policy  = "DROP"
  outbound_policy = "ACCEPT"

  // SSH from anywhere (consider restricting to your IP)
  inbound {
    label    = "ssh"
    action   = "ACCEPT"
    protocol = "TCP"
    ports    = "22"
    ipv4     = ["0.0.0.0/0"]
  }

  // K3s API server
  inbound {
    label    = "k3s"
    action   = "ACCEPT"
    protocol = "TCP"
    ports    = "6443, 6444"
    ipv4     = ["0.0.0.0/0"]
  }

  // K3s API server
  inbound {
    label    = "k3s"
    action   = "ACCEPT"
    protocol = "UDP"
    ports    = "6443, 6444"
    ipv4     = ["0.0.0.0/0"]
  }

  // HTTP/HTTPS for apps
  inbound {
    label    = "http-https"
    action   = "ACCEPT"
    protocol = "TCP"
    ports    = "80,443"
    ipv4     = ["0.0.0.0/0"]
  }

  // NodePort range (optional if you use NodePort services)
  inbound {
    label    = "nodeport"
    action   = "ACCEPT"
    protocol = "TCP"
    ports    = "30000-32767"
    ipv4     = ["0.0.0.0/0"]
  }

  // Internal/cluster traffic (you can narrow this to specific CIDRs later)
  inbound {
    label    = "internal"
    action   = "ACCEPT"
    protocol = "TCP"
    ports    = "1-65535"
    ipv4     = ["0.0.0.0/0"]
  }

  inbound {
    label    = "internal-udp"
    action   = "ACCEPT"
    protocol = "UDP"
    ports    = "1-65535"
    ipv4     = ["0.0.0.0/0"]
  }
}

locals {
  server_ips_sorted = sort(linode_instance.server.ipv4)
}

#########################
# 1) K3S SERVER NODE
#########################

resource "linode_instance" "server" {
  label          = "k3s-server-test"
  region         = "us-southeast"
  type           = "g6-nanode-1"
  image          = "linode/ubuntu24.04"
  private_ip = true
  firewall_id = linode_firewall.dev_fw.id
  root_pass      = var.root_pass
  authorized_keys = [var.ssh_key]

  metadata {
    user_data = base64encode(
      templatefile("${path.module}/cloud-init-server.yaml", {
        K3S_TOKEN = tostring(var.k3s_token)
        K3S_NODE_NAME = "k3s-server-test"
      })
    )
  }

  tags = ["dev"]
}

# Fetch server’s public IP
output "server_ip" {
  value = tolist(linode_instance.server.ipv4)[0]
}

#########################
# 2) K3S WORKER NODES (3x)
#########################

resource "linode_instance" "worker" {
  depends_on = [linode_instance.server]
  count  = 3
  label  = "k3s-worker-${count.index}"
  region = "us-southeast"
  type   = "g6-nanode-1"
  image  = "linode/ubuntu24.04"
  private_ip = true
  firewall_id = linode_firewall.dev_fw.id
  root_pass      = var.root_pass
  authorized_keys = [var.ssh_key]

  metadata {
    user_data = base64encode(
      templatefile("${path.module}/cloud-init-agent.yaml", {
        SERVER_IP = local.server_ips_sorted[1]
        K3S_TOKEN = tostring(var.k3s_token)
        K3S_NODE_NAME = "k3s-worker-${count.index}"
      })
    )
  }

  tags = ["dev"]
}

output "worker_ips" {
  value = [
    for w in linode_instance.worker :
    sort(w.ipv4)[0]
  ]
}

resource "local_file" "k3s_kubeconfig" {
  content  = templatefile("${path.module}/kubeconfig.tpl", {
    SERVER_IP = linode_instance.server.ipv4[0]
  })
  filename = "${path.module}/out/k3s-kubeconfig.yaml"
}

resource "null_resource" "send_kubeconfig" {
  depends_on = [local_file.k3s_kubeconfig]

  connection {
    type        = "ssh"
    host        = linode_instance.mgmt.ipv4[0]
    user        = "root"
    private_key = file(var.private_key_path)
  }

  provisioner "file" {
    source      = "${path.module}/out/k3s-kubeconfig.yaml"
    destination = "/tmp/k3s-kubeconfig.yaml"
  }
}

resource "null_resource" "register_k3s_with_argocd" {
  depends_on = [null_resource.send_kubeconfig]

  connection {
    type        = "ssh"
    host        = linode_instance.mgmt.ipv4[0]
    user        = "root"
    private_key = file(var.private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "echo 'Logging into ArgoCD...'",
      "argocd login ${var.argocd_url} --username admin --password ${var.argocd_password} --insecure",

      "echo 'Removing old cluster entry if present...'",
      "argocd cluster rm k3s-context || true",

      "echo 'Registering new k3s cluster with ArgoCD...'",
      "argocd cluster add k3s-context --kubeconfig /tmp/k3s-kubeconfig.yaml --name k3s"
    ]
  }
}
