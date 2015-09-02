#!/usr/bin/python

import os
import subprocess
import pty
import pexpect
import string
import re
import decimal

from decimal import Decimal

child = pexpect.spawn('crash -s vmcore vmlinux')
child.expect('crash>')


#######################################################################################
#sys output details
######################################################################################


child.sendline('sys|grep DATE')
child.expect('crash>', timeout=30)
crash_time = child.before

child.sendline("'sys|grep CPU |awk '{print $2}''")
child.expect('crash>', timeout=30)
sys_cpu = child.before
#sys_cpu = int(sys_cpu_temp)



#sys_split = sys_cpu.split('\t')
#for sys in sys_split:
#	sys_array = sys.strip().split()
#	sys_cpu1 = int(float(sys_array[2]))

child.sendline('sys|grep NODENAME')
child.expect('crash>', timeout=30)
node_name = child.before

child.sendline('sys|grep RELEASE')
child.expect('crash>', timeout=30)
kernel_ver = child.before
if "el5" in kernel_ver:
	child.sendline("bt -a |grep -e PID -e .text.lock.spinlock -e shrink_zone -e try_to_free_pages")
	child.expect('crash>', timeout=30)
	spinlock_check = child.before
	print spinlock_check
	
	tempcmd = ("bt -a |grep -e PID -e .text.lock.spinlock -e shrink_zone -e try_to_free_pages| grep CPU |wc -l")	
	child.sendline(tempcmd)
        child.expect('crash>', timeout=30)
        spinlock_check_cpu = child.before

	if spinlock_check_cpu == sys_cpu:
		print "All the CPUs have processes trying to acquire spinlock while freeing memory by shrinking memory zones"
	if spinlock_check_cpu != sys_cpu:
		print spinlock_check_cpu, "CPUs, have processes trying to acquire spinlock while freeing memory by shrinking memory zones \n"

	print "try_to_free_pages is invoked if the kernel detects an acute shortage of memory during an operation.\n "
	print "It checks all pages in the current memory zone and frees those least frequently needed "

	print "shrink_zone is the entry point for removing rarely used pages from memory and is called from within \n"
	print "the periodical kswapd mechanism. This method is responsible for two things:" 

	print "It attempts to maintain a balance between the number of active and inactive pages in a zone by moving \n"
	print "pages between the active and inactive lists (using shrink_active_list).  "


if "el6" in kernel_ver:
	print "rhel6"
if "el7" in kernel_ver:
	print "rhel7"

child.sendline("'sys|grep LOAD | awk '{print $3}'|awk -F \. '{print $1}''")
child.expect('crash>', timeout=30)
load1 = child.before

child.sendline("'sys|grep LOAD | awk '{print $4}'|awk -F \. '{print $1}''")
child.expect('crash>', timeout=30)
load5 = child.before

child.sendline("'sys|grep LOAD | awk '{print $5}'|awk -F \. '{print $1}''")
child.expect('crash>', timeout=30)
load15 = child.before

child.sendline("'sys|grep MEMORY'|awk '{print $2}'")
child.expect('crash>', timeout=30)
memory = child.before

child.sendline("'sys|grep PANIC'")
child.expect('crash>', timeout=30)
panic_string = child.before


#######################################################################################
#MEMORY details
#######################################################################################


child.sendline('kmem -i')
child.expect('crash>', timeout=30)
kmem_full = child.before
kmem_split = kmem_full.split('\t')
for kmem in kmem_split:
		kmem_array = kmem.strip().split()
		kmem_total_pages = float(kmem_array[7])
       		kmem_total_free = int(kmem_array[12])
		kmem_total_used = int(kmem_array[20])
		kmem_buffer_used = int(kmem_array[36])
		kmem_cache_used = int(kmem_array[44])
		kmem_slab_used = int(kmem_array[52])
		kmem_swap_total = int(kmem_array[95])
		kmem_swap_used = int(kmem_array[101])
		kmem_swap_free = int(kmem_array[110])

		memory_check = kmem_total_used - kmem_total_free - kmem_buffer_used -kmem_cache_used - kmem_slab_used
		memory_gb = float(memory_check/1048576)

		actual_used = (memory_check*100)/kmem_total_pages
		print "actual memory used :", actual_used

		swap_check = kmem_swap_used - kmem_swap_free
		actual_swap_used = (swap_check*100)/kmem_swap_total
		print "actual swap used:", actual_swap_used

		if actual_used > 95 and actual_swap_used > 80 :
			print "high memory condition"
		else:
			exit()

############################################################################################
#ZONE details
###########################################################################################

child.sendline("kmem -z | grep -i normal |awk '{print $6}'|wc -l")
child.expect('crash>', timeout=30)
total_zone = child.before


child.sendline("kmem -z | grep -i normal |awk '{print $6}'")
child.expect('crash>', timeout=30)
kmem_zone = child.before
kmem_z_split = kmem_zone.split('\t')
for kmem_z in kmem_z_split:
#	for iteration in range(total_zone):
		kmem_zone_array = kmem_z.strip().split()
		kmem_zone_1 = kmem_zone_array[9]
		kmem_zone_2 = kmem_zone_array[10]
#		kmem_zone_3 = kmem_zone_array[25]
		print kmem_zone_1
		print kmem_zone_2
#		print kmem_zone_3


################################################################################################
#MEMORY USAGE details
#################################################################################################

usermem_cmd = str("ps -u -G| sed 's/>//g'| awk '{ total += $8 } END { print total/2^20 }'")
child.sendline(usermem_cmd)
child.expect('crash>', timeout=30)
user_memory_usage = child.before
print "Total RSS for user mode is:", user_memory_usage


child.sendline("ps -G | tail -n +2 | cut -b2- | sort -g -k 8,8 | tail")
child.expect('crash>', timeout=30)
high_memory_consumer = child.before
print high_memory_consumer

memory_check_command = str("ps -G |grep -v PID | sort -n -u -k8 |tail -3 |awk '{print $6,$9}'")
child.sendline(memory_check_command)
child.expect('crash>', timeout=30)
high_mem_consumer = child.before
high_memory_consumer = high_mem_consumer.split('\t')
for high_mem in high_memory_consumer:
		high_mem_array = high_mem.strip().split()
		high_mem_1 = high_mem_array[16]
		high_mem_1_val = high_mem_array[15]
		high_mem_2 = high_mem_array[18]
		high_mem_2_val = high_mem_array[17]
		high_mem_3 = high_mem_array[20]
		high_mem_3_val = high_mem_array[19]
		print high_mem_1_val, high_mem_1
		print high_mem_2_val
		print high_mem_3_val
#		print high_mem_consumer
#		print high_memory_consumer
