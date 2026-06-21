#!/bin/bash
mysql -u root -p -D retinify <<EOF
$(cat create_tables.sql)
EOF <<< "root"