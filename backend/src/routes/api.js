const express = require('express');
const router = express.Router();
const { triggerECSTask } = require('../controllers/ecsController');

// Define the route for triggering ECS task
router.post('/trigger-task', triggerECSTask);

module.exports = router;
