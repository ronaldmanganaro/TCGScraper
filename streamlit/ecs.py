import boto3

# Define ECS client
ecs_client = boto3.client('ecs', region_name='us-east-1')  # Change to your AWS region

# Define ECS parameters
CLUSTER_NAME = "arn:aws:ecs:us-east-1:129871418630:cluster/Bot"  # Replace with your ECS cluster name
TASK_DEFINITION = "PokemonCardPriceCheck:1"  # Replace with your task definition name
SUBNETS = ["subnet-0919a701cc34ed409", "subnet-057cfc4296046f258"]  # Replace with your subnet IDs
SECURITY_GROUPS = ["sg-0cd97d27250af170f"]  # Replace with your security group IDs

def run_ecs_task():
    response = ecs_client.run_task(
        cluster=CLUSTER_NAME,
        launchType="FARGATE",  # Change to "EC2" if using EC2-based ECS tasks
        taskDefinition=TASK_DEFINITION,
        count=1,  # Number of tasks to run
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": SUBNETS,
                "securityGroups": SECURITY_GROUPS,
                "assignPublicIp": "ENABLED"
            }
        }
    )
    
    # Extract task details
    task_arn = response["tasks"][0]["taskArn"]
    print(f"Task started successfully: {task_arn}")
    
    return task_arn