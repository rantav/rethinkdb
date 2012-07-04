#!/usr/bin/env python
import sys, os, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, 'common')))
import driver, http_admin, scenario_common
from vcoptparse import *

op = OptParser()
scenario_common.prepare_option_parser_mode_flags(op)
opts = op.parse(sys.argv)

with driver.Metacluster() as metacluster:
    cluster = driver.Cluster(metacluster)
    executable_path, command_prefix  = scenario_common.parse_mode_flags(opts)
    print "Spinning up a process..."
    files = driver.Files(metacluster, db_path = "db", executable_path = executable_path, command_prefix = command_prefix)
    process = driver.Process(cluster, files, log_path = "log", executable_path = executable_path, command_prefix = command_prefix)
    process.wait_until_started_up()
    cluster.check()
    access = http_admin.ClusterAccess([("localhost", process.http_port)])
    assert access.get_issues() == []
    print "Creating two namespaces with the same name..."
    datacenter = access.add_datacenter()
    access.move_server_to_datacenter(next(iter(access.machines)), datacenter)
    namespace1 = access.add_namespace(primary = datacenter, name = "John Jacob Jingleheimer Schmidt")
    namespace2 = access.add_namespace(primary = datacenter, name = "John Jacob Jingleheimer Schmidt".upper())
    time.sleep(1)
    cluster.check()
    print "Checking that there is an issue about this..."
    issues = access.get_issues()
    assert len(issues) == 1
    assert issues[0]["type"] == "NAME_CONFLICT_ISSUE"
    assert issues[0]["contested_name"].upper() == "John Jacob Jingleheimer Schmidt".upper()
    assert set(issues[0]["contestants"]) == set([namespace1.uuid, namespace2.uuid])
    cluster.check_and_stop()
print "Done."
