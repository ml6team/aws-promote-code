# Login to AWS docker registry

# read profile-id from config-file
config_file="profiles.conf"
source "$config_file"
echo "Profile-Id: $operations"
echo "Profile-Name: operations"

# ======================================================
# Lambda image
# ======================================================

# build docker image (if M1 user --> specify platform)
docker build -t lambda-image -f images/lambda/Dockerfile .
# For running image locally: docker run --rm -ti --platform linux/amd64 training-image

# Login to docker registry
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin $operations.dkr.ecr.eu-west-3.amazonaws.com 

# Tag and Push Docker Image to Container Registry
docker tag lambda-image:latest $operations.dkr.ecr.eu-west-3.amazonaws.com/lambda-image:latest
docker push $operations.dkr.ecr.eu-west-3.amazonaws.com/lambda-image:latest


# # ======================================================
# # Training image
# # ======================================================

# Login to AWS docker registry
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin 763104351884.dkr.ecr.eu-west-3.amazonaws.com

# build docker image (if M1 user --> specify platform)
docker build -t training-image -f images/train/Dockerfile .
# For running image locally: docker run --rm -ti --platform linux/amd64 training-image

# Login to docker registry
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin $operations.dkr.ecr.eu-west-3.amazonaws.com

# Tag and Push Docker Image to Container Registry
docker tag training-image:latest $operations.dkr.ecr.eu-west-3.amazonaws.com/training-image:latest
docker push $operations.dkr.ecr.eu-west-3.amazonaws.com/training-image:latest