apiVersion: v1
kind: Config
preferences: {}

clusters:
- name: ${cluster_name}
  cluster:
    server: https://${server_ip}:6443
    certificate-authority-data: ${ca_data}

users:
- name: ${cluster_name}-user
  user:
    client-certificate-data: ${client_cert}
    client-key-data: ${client_key}

contexts:
- name: ${cluster_name}-context
  context:
    cluster: ${cluster_name}
    user: ${cluster_name}-user

current-context: ${cluster_name}-context
