FROM public.ecr.aws/lambda/python:3.10

# Install Java required by PySpark
RUN yum install -y java-11-amazon-corretto tar gzip && yum clean all
ENV JAVA_HOME=/usr/lib/jvm/java-11-amazon-corretto

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy pipeline directory
COPY pipeline/ ${LAMBDA_TASK_ROOT}/pipeline/

# Set the Lambda handler (Update based on which script this container runs)
CMD ["pipeline.gold_aggregate.main"]