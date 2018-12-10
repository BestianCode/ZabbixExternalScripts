#!/usr/bin/env python3

#**************************** AWS cloud Monitor ******************************
#*
#*  Copyright (c) 2018, Oleg Smirnov <oleg.a.smirnov@gmail.com>
#*  All rights reserved.
#*
#*  Redistribution and use in source and binary forms, with or without
#*  modification, are permitted provided that the following conditions
#*  are met:
#*  1. Redistributions of source code must retain the above copyright
#*     notice, this list of conditions and the following disclaimer.
#*  2. Redistributions in binary form must reproduce the above copyright
#*     notice, this list of conditions and the following disclaimer in the
#*     documentation and/or other materials provided with the distribution.
#*
#*  THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
#*  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#*  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#*  ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
#*  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#*  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
#*  OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
#*  HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#*  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
#*  OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#*  SUCH DAMAGE.
#*
#*****************************************************************************

import re
import sys
import json
import getopt
import datetime
from boto3.session import Session

awsID = ""
awsKey = ""
awsReg = ""
awsMode = ""
awsQuery = ""
namePrefix = ""
awsAdditional = ""

appVersion = "2018.12.10.02"

rdsMetrics = ["CPUUtilization","FreeableMemory","FreeStorageSpace","SwapUsage","WriteThroughput","ReadThroughput","WriteLatency","ReadLatency","DiskQueueDepth","CPUCreditBalance","CPUCreditUsage","DatabaseConnections","ReadIOPS","WriteIOPS","BurstBalance"]
ec2Metrics = ["CPUUtilization","CPUCreditBalance","CPUCreditUsage","NetworkIn","NetworkOut"]
ebsMetrics = ["BurstBalance","VolumeQueueLength","VolumeWriteOps","VolumeReadOps","VolumeWriteBytes","VolumeReadBytes"]
sqsMetrics = ["NumberOfEmptyReceives", "ApproximateAgeOfOldestMessage", "NumberOfMessagesSent", "ApproximateNumberOfMessagesNotVisible", "ApproximateNumberOfMessagesDelayed", "ApproximateNumberOfMessagesVisible", "NumberOfMessagesDeleted", "NumberOfMessagesReceived", "SentMessageSize"]

elbTypes                = ["classic","application"]
elbAssets               = {}
elbAssets[elbTypes[0]]  = ["elb"]
elbAssets[elbTypes[1]]  = ["elbv2"]
elbMetrics              = {}
elbMetrics[elbTypes[0]] = ["HTTPCode_Backend_2XX","HTTPCode_Backend_4XX","HTTPCode_Backend_5XX","HTTPCode_ELB_5XX","EstimatedALBNewConnectionCount","EstimatedALBActiveConnectionCount","UnHealthyHostCount","HealthyHostCount","RequestCount","Latency"]
elbMetrics[elbTypes[1]] = ["RequestCount","ProcessedBytes","ActiveConnectionCount","HTTPCode_Target_4XX_Count","HTTPCode_Target_2XX_Count","HTTPCode_ELB_4XX_Count","HTTPCode_Target_5XX_Count","HTTPCode_Target_3XX_Count","HTTPCode_ELB_5XX_Count","TargetResponseTime","NewConnectionCount","ClientTLSNegotiationErrorCount"]
tgMetrics               = ["RequestCountPerTarget","RequestCount","TargetResponseTime","UnHealthyHostCount","HealthyHostCount","HTTPCode_Target_3XX_Count","HTTPCode_Target_4XX_Count","HTTPCode_Target_2XX_Count","HTTPCode_Target_5XX_Count"]

def about(exitCode=0,additionalMessage=""):
    print(" \
\n \
Copyright (c) 2018, Oleg Smirnov <oleg.a.smirnov@gmail.com>.\n \
Simplified BSD License or FreeBSD License.\n \
v",appVersion,"\n \
\n \
"+sys.argv[0]+" -l <aws access id> -p <aws secret key> -r <aws region> -n <name prefix> -m <mode> -q <query>\n \
\n \
	mode:	query:\n\n \
\n \
	ec2\n \
		getList			[-a 'InstanceID' or -a 'name=InstanceName']\n \
		getInfo			-a 'InstanceID' or -a 'name=InstanceName'\n \
		getVolumesList		-a 'InstanceID' or -a 'name=InstanceName'\n \
		getVolumeInfo		-a 'InstanceID,VolumeID'\n \
\n \
	rds\n \
		getList			[-a 'DatabaseName' or -a 'DatabaseARN']\n \
		getInfo			[-a 'DatabaseName' or -a 'DatabaseARN']\n \
\n \
	ecs\n \
		clustersList\n \
		clusterInfo		-a 'ClusterName'\n \
\n \
		tasksList		-a 'clusterName'\n \
		taskInfo		-a 'ClusterName,TaskName'\n \
\n \
		servicesList		-a 'clusterName'\n \
		serviceInfo		-a 'ClusterName,ServiceName'\n \
\n \
	elb\n \
		getList			[-a 'ELBName']\n \
		getInfo			-a 'ELBName,ELBType'\n \
						    ELBType=(classic|application)\n \
		getTGList		-a 'ELBName'\n \
		getTGInfo		-a 'ELBName,TargetGroupName'\n \
\n \
	s3\n \
		getLatestFiles		-a 'Bucket,Mask,DaysBack'\n \
\n \
	sqs\n \
		getList			[-a 'Part of a queue name']\n \
		getInfo			-a 'QueueName'\n \
\n \
",sep='')
    if additionalMessage!="":
        print("\
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n\
",additionalMessage,"\n\n\
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n",sep='',end='')
    exit(exitCode)

def awsGetCloudWatchJson(rDesc,sess,metrics,namespace,dimensions,arrayName):
    res = sess.client('cloudwatch')
    for x in range(len(metrics)):
        jdoc=res.get_metric_statistics(Period=300,StartTime=(datetime.datetime.utcnow() - datetime.timedelta(seconds=1200)),EndTime=datetime.datetime.utcnow(),MetricName=metrics[x],Namespace=namespace,Statistics=['Average','Minimum','Maximum'],Dimensions=dimensions)
        try:
            lastE=len(jdoc["Datapoints"])-1
            if LastE < 0:
                lastE=0
        except:
            lastE=0
        try:
            jdoc["Datapoints"][lastE]["Average"]
        except:
            rDesc[arrayName+metrics[x]+"Average"]=0
        else:
            rDesc[arrayName+metrics[x]+"Average"]=int(jdoc["Datapoints"][lastE]["Average"])
        try:
            jdoc["Datapoints"][lastE]["Minimum"]
        except:
            rDesc[arrayName+metrics[x]+"Minimum"]=0
        else:
            rDesc[arrayName+metrics[x]+"Minimum"]=int(jdoc["Datapoints"][lastE]["Minimum"])
        try:
            jdoc["Datapoints"][lastE]["Maximum"]
        except:
            rDesc[arrayName+metrics[x]+"Maximum"]=0
        else:
            rDesc[arrayName+metrics[x]+"Maximum"]=int(jdoc["Datapoints"][lastE]["Maximum"])
        try:
            jdoc["Datapoints"][lastE]["Unit"]
        except:
            rDesc[arrayName+metrics[x]+"Unit"]=""
        else:
            rDesc[arrayName+metrics[x]+"Unit"]=str(jdoc["Datapoints"][lastE]["Unit"])
    return rDesc

def awsGetEC2InstanceID(sess,data):
    sData=re.split('=',data)
    if re.search('name', sData[0], re.IGNORECASE):
        res = sess.client('ec2')
        jdoc = res.describe_instances()
        for x in range(len(jdoc["Reservations"])):
            for y in range(len(jdoc["Reservations"][x]["Instances"])):
                for z in range(len(jdoc["Reservations"][x]["Instances"][y]["Tags"])):
                    if jdoc["Reservations"][x]["Instances"][y]["Tags"][z]["Key"] == "Name" and re.search(str(sData[1]), str(jdoc["Reservations"][x]["Instances"][y]["Tags"][z]["Value"]), re.IGNORECASE):
                        return str(jdoc["Reservations"][x]["Instances"][y]["InstanceId"])
    else:
        about(3, 'Wrong additional parameter!')
    about(3, 'The name not found!')

def awsExec(sess,mode,query,prefix,additional):
    rDescArray=[]
#   ----------
#       EC2
#   ----------
    if mode == 'ec2':
        res = sess.client('ec2')
        if query == 'getList':
            try:
                additional
            except:
                jdoc = res.describe_instances()
            else:
                if "=" in additional:
                    jdoc = res.describe_instances(InstanceIds=[awsGetEC2InstanceID(sess,additional)])
                elif "-" in additional:
                    jdoc = res.describe_instances(InstanceIds=[additional])
                else:
                    jdoc = res.describe_instances()
            for x in range(len(jdoc["Reservations"])):
                for y in range(len(jdoc["Reservations"][x]["Instances"])):
                    rDescTemp={}
                    for z in range(len(jdoc["Reservations"][x]["Instances"][y]["Tags"])):
                        if jdoc["Reservations"][x]["Instances"][y]["Tags"][z]["Key"] == "Name":
                            rDescTemp["{#NAME}"]=prefix+"-"+re.sub("\ ","_",jdoc["Reservations"][x]["Instances"][y]["Tags"][z]["Value"])
                            rDescTemp["{#NAMETAG}"]=re.sub("\ ","_",jdoc["Reservations"][x]["Instances"][y]["Tags"][z]["Value"])
                        if jdoc["Reservations"][x]["Instances"][y]["Tags"][z]["Key"] == "Client":
                            rDescTemp["{#CLIENT}"]=jdoc["Reservations"][x]["Instances"][y]["Tags"][z]["Value"]
                    try:
                        rDescTemp["{#CLIENT}"]
                    except:
                        rDescTemp["{#CLIENT}"]=prefix
                    rDescTemp["{#ID}"]=jdoc["Reservations"][x]["Instances"][y]["InstanceId"]
                    rDescTemp["{#STATE}"]=jdoc["Reservations"][x]["Instances"][y]["State"]["Name"]
                    volumeCounter=0
                    rDescVolumesArray=[]
                    for z in range(len(jdoc["Reservations"][x]["Instances"][y]["BlockDeviceMappings"])):
                        if jdoc["Reservations"][x]["Instances"][y]["BlockDeviceMappings"][z]["Ebs"]["Status"] == "attached":
                            rDescVolume={}
                            rDescVolume["{#NUMBER}"]=volumeCounter
                            rDescVolume["{#ID}"]=jdoc["Reservations"][x]["Instances"][y]["BlockDeviceMappings"][z]["Ebs"]["VolumeId"]
                            volumeCounter+=1
                            rDescVolumesArray.append(rDescVolume)
                    rDescTemp["{#VOLUMES}"]=rDescVolumesArray
                    rDescArray.append(rDescTemp)
            print(json.dumps({"data": rDescArray}, indent="\t"))
        elif query == 'getVolumesList':
            try:
                additional
            except:
                about(3,"You have to specify an Instance id or name!")
            else:
                if "=" in additional:
                    jdoc = res.describe_instances(InstanceIds=[awsGetEC2InstanceID(sess,additional)])
                elif "-" in additional:
                    jdoc = res.describe_instances(InstanceIds=[additional])
                else:
                    about(3,"You have to specify an Instance id or name!")
            for x in range(len(jdoc["Reservations"])):
                for y in range(len(jdoc["Reservations"][x]["Instances"])):
                    volumeCounter=0
                    rDescArray=[]
                    for z in range(len(jdoc["Reservations"][x]["Instances"][y]["BlockDeviceMappings"])):
                        if jdoc["Reservations"][x]["Instances"][y]["BlockDeviceMappings"][z]["Ebs"]["Status"] == "attached":
                            rDescTemp={}
                            rDescTemp["{#ID}"]=jdoc["Reservations"][x]["Instances"][y]["InstanceId"]
                            rDescTemp["{#VOLUME}"]=volumeCounter
                            rDescTemp["{#VOLUMEID}"]=jdoc["Reservations"][x]["Instances"][y]["BlockDeviceMappings"][z]["Ebs"]["VolumeId"]
                            volumeCounter+=1
                            rDescArray.append(rDescTemp)
            print(json.dumps({"data": rDescArray}, indent="\t"))
        elif query == 'getInfo':
            try:
                additional
            except:
                about(3,"You have to specify an Instance id or name!")
            else:
                if "=" in additional:
                    jdoc = res.describe_instances(InstanceIds=[awsGetEC2InstanceID(sess,additional)])
                elif "-" in additional:
                    jdoc = res.describe_instances(InstanceIds=[additional])
                else:
                    about(3,"You have to specify an Instance id or name!")
            for x in range(len(jdoc["Reservations"])):
                for y in range(len(jdoc["Reservations"][x]["Instances"])):
                    rDescTemp={}
                    rDescTemp["id"]=jdoc["Reservations"][x]["Instances"][y]["InstanceId"]
                    for z in range(len(jdoc["Reservations"][x]["Instances"][y]["Tags"])):
                        if jdoc["Reservations"][x]["Instances"][y]["Tags"][z]["Key"] == "Name":
                            rDescTemp["Name"]=prefix+"-"+re.sub("\ ","_",jdoc["Reservations"][x]["Instances"][y]["Tags"][z]["Value"])
                            rDescTemp["NameTag"]=re.sub("\ ","_",jdoc["Reservations"][x]["Instances"][y]["Tags"][z]["Value"])
                        if jdoc["Reservations"][x]["Instances"][y]["Tags"][z]["Key"] == "Client":
                            rDescTemp["client"]=jdoc["Reservations"][x]["Instances"][y]["Tags"][z]["Value"]
                    try:
                        rDescTemp["client"]
                    except:
                        rDescTemp["client"]=prefix
                    rDescTemp["type"]=jdoc["Reservations"][x]["Instances"][y]["InstanceType"]
                    rDescTemp["privateIpAddress"]=jdoc["Reservations"][x]["Instances"][y]["PrivateIpAddress"]
                    rDescTemp["publicIpAddress"]=jdoc["Reservations"][x]["Instances"][y]["PublicIpAddress"]
                    rDescTemp["state"]=jdoc["Reservations"][x]["Instances"][y]["State"]["Name"]
                    awsGetCloudWatchJson(rDescTemp,sess,ec2Metrics,'AWS/EC2',[{'Name': 'InstanceId', 'Value': rDescTemp["id"]}],"")
                print(json.dumps(rDescTemp, indent="\t"))
        elif query == 'getVolumeInfo':
            try:
                additional
            except:
                about(3, "You have to specify \"-a\" parameters!")
            else:
                sAdditional=re.split(',',additional)
                try:
                    sAdditional[0]
                except:
                    about(3,"You have to specify an Instance ID!")
                try:
                    sAdditional[1]
                except:
                    about(3,"You have to specify a Volume ID!")
            jdoc = res.describe_instances(InstanceIds=[sAdditional[0]])
            for x in range(len(jdoc["Reservations"])):
                for y in range(len(jdoc["Reservations"][x]["Instances"])):
                    for z in range(len(jdoc["Reservations"][x]["Instances"][y]["BlockDeviceMappings"])):
                        if jdoc["Reservations"][x]["Instances"][y]["BlockDeviceMappings"][z]["Ebs"]["VolumeId"] == sAdditional[1]:
                            rDescTemp={}
                            rDescTemp["id"]=jdoc["Reservations"][x]["Instances"][y]["InstanceId"]
                            rDescTemp["volumeid"]=jdoc["Reservations"][x]["Instances"][y]["BlockDeviceMappings"][z]["Ebs"]["VolumeId"]
                            awsGetCloudWatchJson(rDescTemp,sess,ebsMetrics,'AWS/EBS',[{'Name': 'VolumeId', 'Value': rDescTemp["volumeid"]}],"")
                            break
            print(json.dumps(rDescTemp, indent="\t"))
        else:
            about(3)
#   ----------
#       ECS
#   ----------
    elif mode == 'ecs':
        res = sess.client('ecs')
        if query == 'clustersList':
            jdoc = res.list_clusters()
            for x in range(len(jdoc["clusterArns"])):
                rDescTemp={}
                rDescTemp["{#CNAME}"]=prefix+"-"+re.split("\/",jdoc["clusterArns"][x])[1]
                rDescTemp["{#CLUSTERNAME}"]=re.split("\/",jdoc["clusterArns"][x])[1]
                rDescTemp["{#CLUSTERARN}"]=jdoc["clusterArns"][x]
                jdocI = res.describe_clusters(clusters=[rDescTemp["{#CLUSTERARN}"]])
                for y in range(len(jdocI["clusters"])):
                    if rDescTemp["{#CLUSTERARN}"] == jdocI["clusters"][y]["clusterArn"]:
                        rDescTemp["{#STATUS}"]=jdocI["clusters"][y]["status"]
                        rDescTemp["{#REGISTEREDCONTAINERINSTANCESCOUNT}"]=jdocI["clusters"][y]["registeredContainerInstancesCount"]
                        rDescTemp["{#RUNNINGTASKSCOUNT}"]=jdocI["clusters"][y]["runningTasksCount"]
                        rDescTemp["{#PENDINGTASKSCOUNT}"]=jdocI["clusters"][y]["pendingTasksCount"]
                        rDescTemp["{#ACTIVESERVICESCOUNT}"]=jdocI["clusters"][y]["activeServicesCount"]
                        rDescArray.append(rDescTemp)
                        break
            print(json.dumps({"data": rDescArray}, indent="\t"))
        elif query == 'clusterInfoJ' or query == 'clusterInfo':
            try:
                additional
            except:
                about(3, "You have to specify a Cluster name!")
            jdocI = res.describe_clusters(clusters=[additional])
            rDesc={}
            rDesc["clusterName"]=additional
            rDesc["status"]=jdocI["clusters"][0]["status"]
            rDesc["registeredContainerInstancesCount"]=int(jdocI["clusters"][0]["registeredContainerInstancesCount"])
            rDesc["runningTasksCount"]=int(jdocI["clusters"][0]["runningTasksCount"])
            rDesc["pendingTasksCount"]=int(jdocI["clusters"][0]["pendingTasksCount"])
            rDesc["activeServicesCount"]=int(jdocI["clusters"][0]["activeServicesCount"])
            print(json.dumps(rDesc, indent="\t"))
        elif query == 'tasksList':
            try:
                additional
            except:
                about(3, "You have to specify a Cluster name!")
            jdoc = res.list_tasks(cluster=additional)
            tName=""
            for x in range(len(jdoc["taskArns"])):
                rDescTemp={}
                rDescTemp["{#TASKARN}"]=jdoc["taskArns"][x]
                jdocI = res.describe_tasks(tasks=[rDescTemp["{#TASKARN}"]],cluster=additional)
                for y in range(len(jdocI["tasks"])):
                    if rDescTemp["{#TASKARN}"] == jdocI["tasks"][y]["taskArn"]:
                        """ Number 0 should be investigated !!! """
                        rDescTemp["{#TNAME}"]=prefix+"-"+str(jdocI["tasks"][y]["containers"][0]["name"]) #+"-"+re.split("-", re.split("\/", tName)[1])[4]
                        rDescTemp["{#TASKNAME}"]=str(jdocI["tasks"][y]["containers"][0]["name"]) #+"-"+re.split("-", re.split("\/", tName)[1])[4]
                        rDescTemp["{#CLUSTERARN}"]=jdocI["tasks"][y]["clusterArn"]
                        rDescTemp["{#TASKDEFARN}"]=jdocI["tasks"][y]["taskDefinitionArn"]
                        rDescTemp["{#LSTATUS}"]=jdocI["tasks"][y]["lastStatus"]
                        rDescTemp["{#DSTATUS}"]=jdocI["tasks"][y]["desiredStatus"]
                        rDescTemp["{#CONNECTIVITY}"]=jdocI["tasks"][y]["connectivity"]
                        rDescTemp["{#CPU}"]=int(jdocI["tasks"][y]["cpu"])
                        rDescTemp["{#MEMORY}"]=int(jdocI["tasks"][y]["memory"])
                        rDescTemp["{#GROUP}"]=jdocI["tasks"][y]["group"]
                        rDescArray.append(rDescTemp)
                        break
            print(json.dumps({"data": rDescArray}, indent="\t"))
        elif query == 'taskInfoJ' or query == 'taskInfo':
            try:
                additional
            except:
                about(3, "You have to specify \"-a\" parameters!")
            else:
                sAdditional=re.split(',',additional)
                try:
                    sAdditional[0]
                except:
                    about(3,"You have to specify a Cluster name!")
                try:
                    sAdditional[1]
                except:
                    about(3,"You have to specify a Task name!")
            jdocI = res.describe_tasks(tasks=[sAdditional[1]],cluster=sAdditional[0])
            rDesc={}
            rDesc["clusterName"]=sAdditional[0]
            rDesc["taskName"]=sAdditional[1]
            rDesc["taskDefinitionArn"]=jdocI["tasks"][0]["taskDefinitionArn"]
            rDesc["lastStatus"]=jdocI["tasks"][0]["lastStatus"]
            rDesc["desiredStatus"]=jdocI["tasks"][0]["desiredStatus"]
            rDesc["connectivity"]=jdocI["tasks"][0]["connectivity"]
            rDesc["cpu"]=int(jdocI["tasks"][0]["cpu"])
            rDesc["memory"]=int(jdocI["tasks"][0]["memory"])
            rDesc["group"]=jdocI["tasks"][0]["group"]
            print(json.dumps(rDesc, indent="\t"))
        elif query == 'servicesList':
            try:
                additional
            except:
                about(3, "You have to specify a Cluster name!")
            jdoc = res.list_services(cluster=additional)
            for x in range(len(jdoc["serviceArns"])):
                rDescTemp={}
                rDescTemp["{#SNAME}"]=prefix+"-"+re.split("\/",jdoc["serviceArns"][x])[1]
                rDescTemp["{#SERVICENAME}"]=re.split("\/",jdoc["serviceArns"][x])[1]
                rDescTemp["{#SERVICEARN}"]=jdoc["serviceArns"][x]
                jdocI = res.describe_services(services=[rDescTemp["{#SERVICEARN}"]],cluster=additional)
                for y in range(len(jdocI["services"])):
                    if rDescTemp["{#SERVICEARN}"] == jdocI["services"][y]["serviceArn"]:
                        rDescTemp["{#CLUSTERARN}"]=sClusterArn=jdocI["services"][y]["clusterArn"]
                        rDescTemp["{#STATUS}"]=sStatus=jdocI["services"][y]["status"]
                        rDescTemp["{#DCOUNT}"]=sDesiredCount=jdocI["services"][y]["desiredCount"]
                        rDescTemp["{#RCOUNT}"]=sRunningCount=jdocI["services"][y]["runningCount"]
                        rDescTemp["{#PCOUNT}"]=sPendingCount=jdocI["services"][y]["pendingCount"]
                        rDescArray.append(rDescTemp)
                        break
            print(json.dumps({"data": rDescArray}, indent="\t"))
        elif query == 'serviceInfoJ' or query == 'serviceInfo':
            try:
                additional
            except:
                about(3, "You have to specify \"-a\" parameters!")
            else:
                sAdditional=re.split(',',additional)
                try:
                    sAdditional[0]
                except:
                    about(3,"You have to specify a Cluster name!")
                try:
                    sAdditional[1]
                except:
                    about(3,"You have to specify a Service name!")
            rDesc={}
            rDesc["clusterName"]=sAdditional[0]
            rDesc["serviceName"]=sAdditional[1]
            jdocI = res.describe_services(services=[sAdditional[1]],cluster=sAdditional[0])
            rDesc["status"]=jdocI["services"][0]["status"]
            rDesc["desiredCount"]=jdocI["services"][0]["desiredCount"]
            rDesc["runningCount"]=jdocI["services"][0]["runningCount"]
            rDesc["pendingCount"]=jdocI["services"][0]["pendingCount"]
            rDescTemp={}
            awsGetCloudWatchJson(rDescTemp,sess,['MemoryUtilization'],'AWS/ECS',[{'Name': 'ClusterName', 'Value': sAdditional[0]}, {'Name': 'ServiceName','Value': sAdditional[1]}],"")
            rDesc["memAverage"]=int(rDescTemp["MemoryUtilizationAverage"])
            rDesc["memMaximum"]=int(rDescTemp["MemoryUtilizationMaximum"])
            rDescTemp={}
            awsGetCloudWatchJson(rDescTemp,sess,['CPUUtilization'],'AWS/ECS',[{'Name': 'ClusterName', 'Value': sAdditional[0]}, {'Name': 'ServiceName','Value': sAdditional[1]}],"")
            rDesc["cpuAverage"]=int(rDescTemp["CPUUtilizationAverage"])
            rDesc["cpuMaximum"]=int(rDescTemp["CPUUtilizationMaximum"])
            print(json.dumps(rDesc, indent="\t"))
        else:
            about(3)
#   ----------
#       S3
#   ----------
    elif mode == 's3':
        res = sess.client('s3')
        if query == 'getLatestFiles':
            sAdditional=re.split(',',additional)
            try:
                sAdditional[0]
            except:
                about(3)
            else:
                s3Bucket=sAdditional[0]
            try:
                sAdditional[1]
            except:
                s3Prefix=""
            else:
                s3Prefix=sAdditional[1]
            try:
                sAdditional[2]
            except:
                s3DateBack=0
            else:
                s3DateBack=sAdditional[2]
            jdoc = res.list_objects_v2(Bucket=s3Bucket,Prefix=s3Prefix)
            rDesc={}
            rDesc["count"]=0
            rDesc["files"]=[]
            rDesc["size"]=0
            try:
                jdoc["Contents"]
            except:
                pass
            else:
                for x in range(len(jdoc["Contents"])):
                    s3Date=str(re.split(' ',str(jdoc["Contents"][x]["LastModified"]))[0])
                    dateBack=str(datetime.date.today() - datetime.timedelta(days=int(s3DateBack)))
                    if (s3Date == dateBack):
                        rDesc["count"]+=1
                        rDesc["size"]+=jdoc["Contents"][x]["Size"]
                        rDesc["files"].append(str(jdoc["Contents"][x]["Key"]))
            print(json.dumps(rDesc, indent="\t"))
        else:
            about(3)
#   ----------
#       RDS
#   ----------
    elif mode == 'rds':
        res = sess.client('rds')
        if query == 'getList':
            try:
                additional
            except:
                jdoc = res.describe_db_instances()
            else:
                jdoc = res.describe_db_instances(DBInstanceIdentifier=additional)
            for x in range(len(jdoc["DBInstances"])):
                rDesc={}
                rDesc["{#RINAME}"]=jdoc["DBInstances"][x]["DBInstanceIdentifier"]
                rDesc["{#ARN}"]=jdoc["DBInstances"][x]["DBInstanceArn"]
                rDesc["{#HOST}"]=jdoc["DBInstances"][x]["Endpoint"]["Address"]
                rDesc["{#PORT}"]=jdoc["DBInstances"][x]["Endpoint"]["Port"]
                rDescArray.append(rDesc)
            print(json.dumps({"data": rDescArray}, indent="\t"))
        elif query == 'getInfo':
            try:
                additional
            except:
                jdoc = res.describe_db_instances()
            else:
                jdoc = res.describe_db_instances(DBInstanceIdentifier=additional)
            for x in range(len(jdoc["DBInstances"])):
                rDesc={}
                rDesc["identifier"]=jdoc["DBInstances"][x]["DBInstanceIdentifier"]
                rDesc["status"]=jdoc["DBInstances"][x]["DBInstanceStatus"]
                rDesc["host"]=jdoc["DBInstances"][x]["Endpoint"]["Address"]
                rDesc["port"]=jdoc["DBInstances"][x]["Endpoint"]["Port"]
                rDesc["storage"]=jdoc["DBInstances"][x]["AllocatedStorage"]
                rDesc["maz"]=jdoc["DBInstances"][x]["MultiAZ"]
                rDesc["engine"]=jdoc["DBInstances"][x]["Engine"]
                rDesc["version"]=jdoc["DBInstances"][x]["EngineVersion"]
                awsGetCloudWatchJson(rDesc,sess,rdsMetrics,'AWS/RDS',[{'Name': 'DBInstanceIdentifier', 'Value': rDesc["identifier"]}],"")
                rDescArray.append(rDesc)
            print(json.dumps({"data": rDescArray}, indent="\t"))
        else:
            about(3)
#   ----------
#       ELB
#   ----------
    elif mode == 'elb':
        if query == 'getList':
            res1 = sess.client('elb')
            res2 = sess.client('elbv2')
            try:
                additional
            except:
                jdoc1 = res1.describe_load_balancers()
                jdoc2 = res2.describe_load_balancers()
            else:
                if additional == "":
                    jdoc1 = res1.describe_load_balancers()
                    jdoc2 = res2.describe_load_balancers()
                else:
                    try:
                        jdoc1 = res1.describe_load_balancers(LoadBalancerNames=[additional])
                    except:
                        jdoc1 = ""
                    try:
                        jdoc2 = res2.describe_load_balancers(Names=[additional])
                    except:
                        jdoc2 = ""
            try:
                for x in range(len(jdoc1["LoadBalancerDescriptions"])):
                    rDesc={}
                    rDesc["{#NAME}"]=jdoc1["LoadBalancerDescriptions"][x]["LoadBalancerName"]
                    rDesc["{#DNS}"]=jdoc1["LoadBalancerDescriptions"][x]["DNSName"]
                    rDesc["{#TYPE}"]="classic"
                    rDesc["{#SCHEME}"]=jdoc1["LoadBalancerDescriptions"][x]["Scheme"]
                    rDesc["{#ARN}"]=""
                    rDescArray.append(rDesc)
            except:
                pass
            try:
                for x in range(len(jdoc2["LoadBalancers"])):
                    rDesc={}
                    rDesc["{#NAME}"]=jdoc2["LoadBalancers"][x]["LoadBalancerName"]
                    rDesc["{#DNS}"]=jdoc2["LoadBalancers"][x]["DNSName"]
                    rDesc["{#TYPE}"]="application"
                    rDesc["{#SCHEME}"]=jdoc2["LoadBalancers"][x]["Scheme"]
                    rDesc["{#ARN}"]=jdoc2["LoadBalancers"][x]["LoadBalancerArn"]
                    rDescArray.append(rDesc)
            except:
                pass
            print(json.dumps({"data": rDescArray}, indent="\t"))
        elif query == 'getInfo':
            try:
                additional
            except:
                about(3, "You have to specify \"-a\" parameters!")
            else:
                if "," not in additional:
                    about(3, "You have to specify \"-a\" parameters! Read help!")
                sAdditional=re.split(',',additional)
                try:
                    sAdditional[0]
                except:
                    about(3,"You have to specify a load balancer name!")
                try:
                    sAdditional[1]
                except:
                    about(3,"You have to specify one of load balancer types: "+str(elbTypes))
            if sAdditional[1] in elbTypes:
                res = sess.client(elbAssets[sAdditional[1]][0])
            else:
                about(3,"You have to specify one of load balancer types: "+str(elbTypes))
            rDesc={}
            if sAdditional[1] == elbTypes[0]:
                jdoc = res.describe_instance_health(LoadBalancerName=sAdditional[0])
                rDesc["name"]=sAdditional[0]
                rDesc["instances"]=len(jdoc["InstanceStates"])
                rDesc["instancesHealthy"]=0
                rDesc["instancesUnHealthy"]=0
                for x in range(rDesc["instances"]):
                    if re.search('InService', jdoc["InstanceStates"][x]["State"], re.IGNORECASE):
                        rDesc["instancesHealthy"]+=1
                    else:
                        rDesc["instancesUnHealthy"]+=1
                awsGetCloudWatchJson(rDesc,sess,elbMetrics[elbTypes[0]],'AWS/ELB',[{'Name': 'LoadBalancerName','Value': sAdditional[0]}],"")
                print(json.dumps(rDesc, indent="\t"))
            elif sAdditional[1] == elbTypes[1]:
                jdoc = res.describe_load_balancers(Names=[sAdditional[0]])
                rDesc["arn"] = jdoc["LoadBalancers"][0]["LoadBalancerArn"]
                rDescTemp=re.split("/", jdoc["LoadBalancers"][0]["LoadBalancerArn"])
                rDesc["sname"] = rDescTemp[1]+"/"+rDescTemp[2]+"/"+rDescTemp[3]
                rDesc["name"] = jdoc["LoadBalancers"][0]["LoadBalancerName"]
                awsGetCloudWatchJson(rDesc,sess,elbMetrics[elbTypes[1]],'AWS/ApplicationELB',[{'Name': 'LoadBalancer','Value': rDesc["sname"]}],"")
                print(json.dumps(rDesc, indent="\t"))
        elif query == 'getTGList':
            try:
                additional
            except:
                about(3,"You have to specify a load balancer name!")
            res = sess.client(elbAssets[elbTypes[1]][0])
            jdocA = res.describe_load_balancers(Names=[additional])
            jdoc = res.describe_target_groups(LoadBalancerArn=str(jdocA["LoadBalancers"][0]["LoadBalancerArn"]))
            for x in range(len(jdoc["TargetGroups"])):
                rDesc={}
                rDesc["{#NAME}"] = jdoc["TargetGroups"][x]["TargetGroupName"]
                rDesc["{#ARN}"] = jdoc["TargetGroups"][x]["TargetGroupArn"]
                rDesc["{#ELBNAME}"] = jdocA["LoadBalancers"][0]["LoadBalancerName"]
                rDesc["{#ELBARN}"] = jdocA["LoadBalancers"][0]["LoadBalancerArn"]
                rDescArray.append(rDesc)
            print(json.dumps({"data": rDescArray}, indent="\t"))
        elif query == 'getTGInfo':
            try:
                additional
            except:
                about(3, "You have to specify \"-a\" parameters!")
            else:
                if "," not in additional:
                    about(3, "You have to specify \"-a\" parameters! Read help!")
                sAdditional=re.split(',',additional)
                try:
                    sAdditional[0]
                except:
                    about(3,"You have to specify a load balancer short name!")
                try:
                    sAdditional[1]
                except:
                    about(3,"You have to specify a target group short name!")
            res = sess.client(elbAssets[elbTypes[1]][0])
            jdoc = res.describe_load_balancers(Names=[sAdditional[0]])
            rDesc={}
            rDescTemp=re.split("/", jdoc["LoadBalancers"][0]["LoadBalancerArn"])
            rDesc["elbSName"] = rDescTemp[1]+"/"+rDescTemp[2]+"/"+rDescTemp[3]
            rDesc["elbArn"] = jdoc["LoadBalancers"][0]["LoadBalancerArn"]
            jdoc = res.describe_target_groups(LoadBalancerArn=rDesc["elbArn"])
            for x in range(len(jdoc["TargetGroups"])):
                if jdoc["TargetGroups"][x]["TargetGroupName"] == sAdditional[1]:
                    rDescTemp = re.split("/", jdoc["TargetGroups"][x]["TargetGroupArn"])
                    rDescTemp = re.split(":", str(rDescTemp[0]+"/"+rDescTemp[1]+"/"+rDescTemp[2]))
                    rDesc["tgSName"] = rDescTemp[len(rDescTemp)-1]
                    rDesc["tgArn"] = jdoc["TargetGroups"][x]["TargetGroupArn"]
                    break
            rDesc["all"]=0
            rDesc["healthy"]=0
            rDesc["unhealthy"]=0
            jdoc = res.describe_target_health(TargetGroupArn=rDesc["tgArn"])
            for y in range(len(jdoc["TargetHealthDescriptions"])):
                rDesc["all"]+=1
                if jdoc["TargetHealthDescriptions"][y]["TargetHealth"]["State"] == "healthy":
                    rDesc["healthy"]+=1
                else:
                    rDesc["unhealthy"]+=1
            awsGetCloudWatchJson(rDesc,sess,tgMetrics,'AWS/ApplicationELB',[{'Name': 'LoadBalancer','Value': rDesc["elbSName"]}, {'Name': 'TargetGroup','Value': rDesc["tgSName"]}],"")
            print(json.dumps(rDesc, indent="\t"))
#   ----------
#       SQS
#   ----------
    elif mode == 'sqs':
        if query == 'getList':
            res = sess.client('sqs')
            jdoc = res.list_queues()
            try:
                additional
            except:
                additional=""
            for x in range(len(jdoc["QueueUrls"])):
                if additional == "":
                    rDesc={}
                    rDesc["{#QURL}"]=jdoc["QueueUrls"][x]
                    x=re.split("\/", jdoc["QueueUrls"][x])
                    rDesc["{#QNAME}"]=x[len(x)-1]
                    rDescArray.append(rDesc)
                else:
                    if additional in jdoc["QueueUrls"][x]:
                        rDesc={}
                        rDesc["{#QURL}"]=jdoc["QueueUrls"][x]
                        x=re.split("\/", jdoc["QueueUrls"][x])
                        rDesc["{#QNAME}"]=x[len(x)-1]
                        rDescArray.append(rDesc)
            print(json.dumps({"data": rDescArray}, indent="\t"))
        elif query == 'getInfo':
            res = sess.client('sqs')
            try:
                additional
            except:
                about(3,"You have to specify a queue name!")
            jdoc = res.list_queues(QueueNamePrefix=additional)
            rDesc={}
            rDesc["url"]=jdoc["QueueUrls"][0]
            jdoc = res.get_queue_attributes(QueueUrl=rDesc["url"],AttributeNames=["All"])
            rDesc["ApproximateNumberOfMessages"]=jdoc["Attributes"]["ApproximateNumberOfMessages"]
            rDesc["ApproximateNumberOfMessagesNotVisible"]=jdoc["Attributes"]["ApproximateNumberOfMessagesNotVisible"]
            rDesc["ApproximateNumberOfMessagesDelayed"]=jdoc["Attributes"]["ApproximateNumberOfMessagesDelayed"]
            rDesc["MaximumMessageSize"]=jdoc["Attributes"]["MaximumMessageSize"]
            rDesc["MessageRetentionPeriod"]=jdoc["Attributes"]["MessageRetentionPeriod"]
            awsGetCloudWatchJson(rDesc,sess,sqsMetrics,'AWS/SQS',[{'Name': 'QueueName','Value': additional}],"")
            print(json.dumps(rDesc, indent="\t"))
        else:
            about(3)
    else:
        about(3)

try:
    opts, args = getopt.getopt(sys.argv[1:],"hl:p:r:m:q:a:n:o:")
except getopt.GetoptError:
    about(2)

for opt, arg in opts:
    if opt == '-h':
        about(0)
    elif opt == "-l":
        awsID = arg
    elif opt == "-p":
        awsKey = arg
    elif opt in ("-r", "--region"):
        awsReg = arg
    elif opt in ("-n", "--prefix"):
        namePrefix = arg
    elif opt in ("-m", "--mode"):
        awsMode = arg
    elif opt in ("-q", "--query"):
        awsQuery = arg
    elif opt in ("-a", "--additional"):
        awsAdditional = arg

if (awsID == "") or (awsKey == "") or (awsReg == "") or (namePrefix == "") or (awsMode == "") or (awsQuery == ""):
    about(1)

session = Session(aws_access_key_id=awsID,aws_secret_access_key=awsKey,region_name=awsReg)
awsExec(session,awsMode,awsQuery,namePrefix,awsAdditional)

