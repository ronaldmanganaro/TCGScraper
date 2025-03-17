
# Start runner
C:\Users\MrCool\Documents\Repos\actions-runner\run.cmd

# Set the env
[System.Environment]::SetEnvironmentVariable("VOLUME_PATH", "C:\Users\WinMax2\Documents\Repos\postgres\data")
docker-compose up -d
