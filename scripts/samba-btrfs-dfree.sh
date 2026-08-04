#!/bin/bash

btrfs qgroup show -reF --raw "$1" | tail -1 | awk '{print $4/1024, ($4-$2)/1024}'
