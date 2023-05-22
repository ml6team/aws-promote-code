# Login to AWS docker registry
# aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin 763104351884.dkr.ecr.eu-west-3.amazonaws.com
echo "Account-Id: 123971416876"
echo "Profile-Name: operations"

# ======================================================
# Lambda image
# ======================================================

# build docker image (if M1 user --> specify platform)
docker build -t lambda-image -f images/lambda/Dockerfile .
# For running image locally: docker run --rm -ti --platform linux/amd64 training-image

# Login to docker registry
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin 123971416876.dkr.ecr.eu-west-3.amazonaws.com 

# # Create Amazon Elastic Container Registry Repository
# aws ecr create-repository --region eu-west-3 --repository-name lambda-image --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE 

# Tag and Push Docker Image to Container Registry
docker tag lambda-image:latest 123971416876.dkr.ecr.eu-west-3.amazonaws.com/lambda-image:latest
docker push 123971416876.dkr.ecr.eu-west-3.amazonaws.com/lambda-image:latest


# # ======================================================
# # Training image
# # ======================================================

# Login to AWS docker registry
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin 763104351884.dkr.ecr.eu-west-3.amazonaws.com

# build docker image (if M1 user --> specify platform)
docker build -t training-image -f images/train/Dockerfile .
# For running image locally: docker run --rm -ti --platform linux/amd64 training-image

# Login to docker registry
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin 123971416876.dkr.ecr.eu-west-3.amazonaws.com

# Create Amazon Elastic Container Registry Repository
# aws ecr create-repository --region eu-west-3 --repository-name training-image --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

# Tag and Push Docker Image to Container Registry
docker tag training-image:latest 123971416876.dkr.ecr.eu-west-3.amazonaws.com/training-image:latest
docker push 123971416876.dkr.ecr.eu-west-3.amazonaws.com/training-image:latest