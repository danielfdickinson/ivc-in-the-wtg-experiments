#!/bin/sh

ip6_addr=""
dns_server="$(resolvectl dns ens3|cut -f2 -d:|tr -d ' ')"

while [ -z "$ip6_addr" ]; do
  ip6_addr="$(host -t aaaa ${query_addr} $dns_server|tail -n1)"
  if echo "$ip6_addr" | grep -q "not found"; then
    ip6_addr=""
  else
    ip6_addr="$${ip6_addr##* }"
  fi
done

cat >/etc/netplan/51-cloud-init-ipv6.yaml <<EOF
network:
  version: 2
  ethernets: 
    ens3:
      dhcp6: false
      addresses:
        - $${ip6_addr}/128
      routes:
        - to: ::/0
          via: {{ gw6 }}
          on-link: true
EOF

systemctl disable --now set-ipv6-netplan-once.timer
systemctl stop wg-quick@wg0 || true
sleep 2
netplan apply
sleep 2
if [ "$(systemctl is-enabled wg-quick@wg0)" = "enabled" ]; then systemctl start wg-quick@wg0; else true; fi
