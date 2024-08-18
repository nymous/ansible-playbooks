# Ansible Playbooks

## Local requirements

- `c-lolcat`

## Manual prerequisites

```shell
# Rename user/group and move home dir
# See https://www.serverlab.ca/tutorials/linux/administration-linux/how-to-rename-linux-users-and-their-home-directory/
usermod --login nymous debian
usermod --home /home/nymous --move-home nymous
groupmod --new-name nymous debian

# Set passwords for nymous and root
passwd nymous
passwd
```

## TODO

- [x] Common tools
- [x] Firewall
- [x] Wireguard
- [x] Gitolite
- [ ] Fail2ban
- [x] Certbot
- [ ] Nginx
- [ ] HAProxy?
- [ ] Netdata
- [ ] Borg Backup
- [ ] PostgreSQL
- [ ] Nextcloud
- [ ] Jackett
- [ ] Atuin server
- [ ] Atuin client
- [ ] CrBot
- [ ] OpenVPN
- [x] Mosh

## Netdata

https://learn.netdata.cloud/docs/installing/one-line-installer-for-all-linux-systems
https://learn.netdata.cloud/docs/installing/native-linux-distribution-packages#manual-setup-of-deb-packages
https://learn.netdata.cloud/docs/installing/install-with-a-cicd-provisioning-system/ansible
https://github.com/netdata/community/blob/main/configuration-management/ansible-quickstart/README.md
https://learn.netdata.cloud/docs/configuring/common-configuration-changes
https://learn.netdata.cloud/docs/configuring/securing-netdata-agents
https://blog.netdata.cloud/the-reality-of-netdatas-long-term-metrics-storage-database/
https://learn.netdata.cloud/docs/configuring/securing-netdata-agents/reverse-proxies/nginx
https://learn.netdata.cloud/docs/configuring/optimizing-metrics-database/change-how-long-netdata-stores-metrics#calculate-the-system-resources-ram-disk-space-needed-to-store-metrics

```sh
  cloud_prefix="${INSTALL_PREFIX}/var/lib/netdata/cloud.d"

  run_as_root mkdir -p "${cloud_prefix}"

  cat > "${tmpdir}/cloud.conf" << EOF
[global]
  enabled = no
EOF




sh netdata-kickstart.sh --dry-run --native-only

/usr/bin/curl --fail -q -sSL --connect-timeout 10 --retry 3 --output /tmp/netdata-kickstart-l42C8HD81f/netdata-repo-edge_2-2+debian12_all.deb https://repo.netdata.cloud/repos/repoconfig/debian/bookworm/netdata-repo-edge_2-2+debian12_all.deb

apt-get install /tmp/netdata-kickstart-l42C8HD81f/netdata-repo-edge_2-2+debian12_all.deb

apt-get install netdata

test -x //usr/libexec/netdata/netdata-updater.sh
grep -q \-\-enable-auto-updates //usr/libexec/netdata/netdata-updater.sh
/usr/libexec/netdata/netdata-updater.sh --enable-auto-updates
```
