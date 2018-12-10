# Amazon AWS (EC2, RDS, ECS, ELB, S3, SQS and CloudWatch) Monitoring script!

## Requirements:
 * Python >= 3.5
 * Boto3 library >= 1.9.45

## Script usage

### Help:

~~~
./cloudWatch.py -l <aws access id> -p <aws secret key> -r <aws region> -n <name prefix> -m <mode> -q <query>

    mode:	query:

    ec2
	getList			[-a 'InstanceID' or -a 'name=InstanceName']
	getInfo			-a 'InstanceID' or -a 'name=InstanceName'
	getVolumesList		-a 'InstanceID' or -a 'name=InstanceName'
	getVolumeInfo		-a 'InstanceID,VolumeID'
 
    rds
	getList			[-a 'DatabaseName' or -a 'DatabaseARN']
	getInfo			[-a 'DatabaseName' or -a 'DatabaseARN']
 
    ecs
	clustersList
	clusterInfo		-a 'ClusterName'
 
	tasksList		-a 'clusterName'
	taskInfo		-a 'ClusterName,TaskName'
 
	servicesList		-a 'clusterName'
	serviceInfo		-a 'ClusterName,ServiceName'
 
    elb
	getList			[-a 'ELBName']
	getInfo			-a 'ELBName,ELBType'
			    ELBType=(classic|application)
	getTGList		-a 'ELBName'
	getTGInfo		-a 'ELBName,TargetGroupName'
 
    s3
	getLatestFiles		-a 'Bucket,Mask,DaysBack'
 
    sqs
	getList			[-a 'QueueName']
	getInfo			-a 'QueueName'
~~~

### Examples:

```./cloudWatch.py -l "AccessKey" -p "SecretKey" -r us-west-2 -n Client1 -m elb -q getList```

~~~
{
    "data": [
	{
	    "{#NAME}": "Staging",
	    "{#DNS}": "Staging-1234567.us-west-2.elb.amazonaws.com",
	    "{#TYPE}": "classic",
	    "{#SCHEME}": "internet-facing",
	    "{#ARN}": ""
	},
	{
	    "{#NAME}": "Production",
	    "{#DNS}": "Production-1234567.us-west-2.elb.amazonaws.com",
	    "{#TYPE}": "classic",
	    "{#SCHEME}": "internet-facing",
	    "{#ARN}": ""
	}
    ]
}
~~~

```./cloudWatch.py -l "AccessKey" -p "SecretKey" -r us-west-2 -n Client1 -m elb -q getInfo -a "Production,classic"```

~~~
{
    "name": "Production",
    "instances": 2,
    "instancesHealthy": 2,
    "instancesUnHealthy": 0,
    "HTTPCode_Backend_2XXAverage": 1,
    "HTTPCode_Backend_2XXMinimum": 0,
    "HTTPCode_Backend_2XXMaximum": 0,
    "HTTPCode_Backend_2XXUnit": "Count",
    "HTTPCode_Backend_4XXAverage": 0,
    "HTTPCode_Backend_4XXMinimum": 0,
    "HTTPCode_Backend_4XXMaximum": 0,
    "HTTPCode_Backend_4XXUnit": "",
    "HTTPCode_Backend_5XXAverage": 0,
    "HTTPCode_Backend_5XXMinimum": 0,
    "HTTPCode_Backend_5XXMaximum": 0,
    "HTTPCode_Backend_5XXUnit": "",
    "HTTPCode_ELB_5XXAverage": 0,
    "HTTPCode_ELB_5XXMinimum": 0,
    "HTTPCode_ELB_5XXMaximum": 0,
    "HTTPCode_ELB_5XXUnit": "",
    "EstimatedALBNewConnectionCountAverage": 30,
    "EstimatedALBNewConnectionCountMinimum": 20,
    "EstimatedALBNewConnectionCountMaximum": 48,
    "EstimatedALBNewConnectionCountUnit": "Count",
    "EstimatedALBActiveConnectionCountAverage": 5,
    "EstimatedALBActiveConnectionCountMinimum": 5,
    "EstimatedALBActiveConnectionCountMaximum": 6,
    "EstimatedALBActiveConnectionCountUnit": "Count",
    "UnHealthyHostCountAverage": 1,
    "UnHealthyHostCountMinimum": 1,
    "UnHealthyHostCountMaximum": 1,
    "UnHealthyHostCountUnit": "Count",
    "HealthyHostCountAverage": 1,
    "HealthyHostCountMinimum": 1,
    "HealthyHostCountMaximum": 1,
    "HealthyHostCountUnit": "Count",
    "RequestCountAverage": 1,
    "RequestCountMinimum": 1,
    "RequestCountMaximum": 1,
    "RequestCountUnit": "Count",
    "LatencyAverage": 0,
    "LatencyMinimum": 0,
    "LatencyMaximum": 0,
    "LatencyUnit": "Seconds"
}
~~~

## Macro variables for zabbix hosts and templates

### Shared:

* {$AWSACCESS} - AWS Access key
* {$AWSREGION} - AWS Region
* {$AWSSECRET} - AWS Secret key
* {$PREFIX}    - This prefix will be added to begin of some trigger names. Usually it should be different for hosts or group hosts.

### S3 Backups checker

* {$AWSBUCKET} - AWS Bucket
* {$BACKUPMASK} - file mask

### EC2

* {$INSTANCEID} - Instance ID or tage 'Name'

### ECS

* {$CLUSTERNAME} - ECS Cluster name

### RDS

* {$RDSNAME} - RDS Instance name

### ELB

* {$ELBNAME} - LoadBalancer name

### SQS

* {$SQSNAME} - Name of the sqs queue or part of the name: "queue-xxx-dev-yyy" or just "dev"

# Additional templates:

## Testing alets

* `templates/SendTestAlert.xml` - Periodic sending testing alerts.

## Check SSL Certificates

* `ssl-cert-days.sh <DNSHostName> [Port]` - Check of a number of the days until SSL Certificate expiration.
* `ssl-cert-status.sh <DNSHostName> [Port]` - Validate SSL Certifilate. 1 - is valid, 0 - is invalid.
* `templates/ssl.c.check.xml` - template
