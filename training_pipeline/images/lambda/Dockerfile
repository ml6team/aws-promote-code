FROM public.ecr.aws/lambda/python:3.8

# Install the function's dependencies 
COPY images/lambda/requirements.txt .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY deploy.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "deploy.lambda_func" ]