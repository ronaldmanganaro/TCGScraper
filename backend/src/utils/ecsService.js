const AWS = require('aws-sdk');

// Initialize ECS client
const ecs = new AWS.ECS({ region: process.env.AWS_REGION });

const startECSTask = async () => {
  const params = {
    cluster: process.env.ECS_CLUSTER_NAME,   // Your ECS cluster name
    taskDefinition: process.env.ECS_TASK_DEFINITION, // Your ECS task definition ARN
    count: 1,  // Number of tasks to run
    launchType: 'FARGATE',  // Or 'EC2', depending on your setup
    networkConfiguration: {
      awsvpcConfiguration: {
        subnets: [process.env.ECS_SUBNET_ID],  // Your VPC subnet
        assignPublicIp: 'ENABLED',
      },
    },
  };

  try {
    const result = await ecs.runTask(params).promise();
    return result;
  } catch (error) {
    throw new Error('Error triggering ECS task: ' + error.message);
  }
};

module.exports = { startECSTask };
