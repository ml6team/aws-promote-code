# read profile-id from config-file
config_file="profiles.conf"
source "$config_file"
echo "Profile-Id: $operations"
echo "Profile-Name: operations"

# build docker image (if running on M1/M2 --> specify platform with : --platform linux/amd64)
docker build -t lambda-image -f images/lambda/Dockerfile .

# Login to docker registry
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin $operations.dkr.ecr.eu-west-3.amazonaws.com 

# Tag and Push Docker Image to Container Registry
docker tag lambda-image:latest $operations.dkr.ecr.eu-west-3.amazonaws.com/lambda-image:latest
docker push $operations.dkr.ecr.eu-west-3.amazonaws.com/lambda-image:latest