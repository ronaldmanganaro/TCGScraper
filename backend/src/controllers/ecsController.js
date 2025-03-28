const { startECSTask } = require('../utils/ecsService');

// Controller to trigger ECS task
const triggerECSTask = async (req, res) => {
  try {
    const response = await startECSTask();
    res.status(200).json({ message: 'ECS task triggered successfully', data: response });
  } catch (error) {
    res.status(500).json({ message: 'Failed to trigger ECS task', error: error.message });
  }
};

module.exports = { triggerECSTask };
