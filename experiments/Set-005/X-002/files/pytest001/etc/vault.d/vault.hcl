ui = false

mlock = true

storage "file" {
  path = "/opt/vault/data"
}

# HTTP listener - localhost
listener "tcp" {
  address = "127.0.0.1:8200"
  tls_disable = 1
}
