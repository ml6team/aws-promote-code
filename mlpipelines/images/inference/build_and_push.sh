
# Login to AWS docker registry
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin 763104351884.dkr.ecr.eu-west-3.amazonaws.com

# build docker image (if M1 user --> specify platform)
docker build -t inference-image --platform linux/amd64 -f images/train/Dockerfile .
# For running image locally: docker run --rm -ti --platform linux/amd64 inference-image

# Login to docker registry
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin 101436505502.dkr.ecr.eu-west-3.amazonaws.com

# Create Amazon Elastic Container Registry Repository
aws ecr create-repository --repository-name inference-image --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE --region eu-west-3

# Tag and Push Docker Image to Container Registry
docker tag inference-image:latest 101436505502.dkr.ecr.eu-west-3.amazonaws.com/inference-image:latest
docker push 101436505502.dkr.ecr.eu-west-3.amazonaws.com/inference-image:latest