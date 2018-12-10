#!/bin/sh

host=$1
cport="0${x}"

if [ ${cport} -gt 0 ] && [ ${cport} -lt 65535 ]; then
    port=${cport}
else
    port=443
fi

/usr/local/etc/zabbix/zabbix/externalscripts/tools/ssl-cert-check/ssl-cert-check -s ${host} -p ${port} -n | awk '{ print $2 }' | grep -iE "valid|Expiring" | wc -l | sed 's/[^0-9]//g'
