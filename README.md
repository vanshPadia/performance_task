# vansh-pip

General configuration Info

Description -
Memory
128MB
Ephemeral storage
512MB
Timeout
5min3sec
SnapStart
Info
None

{
"Version": "2012-10-17",
"Statement": [
{
"Effect": "Allow",
"Action": [
"autoscaling:CompleteLifecycleAction"
],
"Resource": "arn:aws:autoscaling:_:313686187887:autoScalingGroup:_:autoScalingGroupName/asg-dev-impressico"
},
{
"Effect": "Allow",
"Action": [
"ssm:SendCommand"
],
"Resource": [
"arn:aws:ssm:*:*:document/AWS-RunShellScript",
"arn:aws:ec2:*:*:instance/*"
]
},
{
"Effect": "Allow",
"Action": [
"ssm:GetCommandInvocation"
],
"Resource": "\*"
}
]
}

{
"Version": "2012-10-17",
"Statement": [
{
"Effect": "Allow",
"Action": [
"logs:CreateLogGroup",
"logs:CreateLogStream",
"logs:PutLogEvents"
],
"Resource": "\*"
}
]
}
