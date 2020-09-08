storage "file" {
    path = "/etc/vault/database"
}

listener "tcp" {
    address = "0.0.0.0:8200"
    tls_disable = 1
}


log_level = "debug"