<div style="display: flex; justify-content: center;">
  <img src="readme_images/ML6_black_round.png" alt="Image 1" width="40px" style="margin-right: 10px;">
  <img src="https://skillicons.dev/icons?i=aws" alt="Image 2" width="40px">
</div>
<br>
<h1 align="center">AWS MLOps Artifact by ML6 </h1>
Within this repository, ML6 presents a comprehensive template for MLOps projects on AWS. Our aim is to showcase ML6's preferred approach, where code promotion takes precedence over model promotion across different environments. This approach offers several notable advantages:

- Model and supporting code such as inference pipelines can follow the same staging pattern.
- Training code is reviewed and retraining can be automated in production.
- Staging of time series pipeline can be unified with regression/classification.
- Production data access in development environment is not needed.

By embracing this code promotion strategy, ML6 aims to establish a standardized and efficient MLOps workflow, promoting best practices in model development, deployment, and maintenance on the AWS platform.

# 1. Project structure
This project comprises three distinct environments and a total of four AWS accounts, each serving specific purposes:

1. **Development:** This environment is dedicated to the development phase of the project, where code changes and enhancements are implemented and tested.

2. **Staging:** The staging environment serves as an intermediate stage for testing and quality assurance. It allows for thorough validation of code and functionality before deployment to the production environment.

3. **Production:** The production environment is the live, operational environment where the application or system is accessible to end-users and delivers its intended functionality.

In addition to the three environments, there is also:

4. **Operations Account:** This account is responsible for running continuous integration and deployment (CI/CD) processes. It serves as the central hub for hosting artifacts and resources that need to be promoted across the various environments.

By employing this account structure, we can ensure proper segregation of responsibilities and enable efficient promotion of artifacts from the operations account to the desired environments, following the established code promotion approach.

# 2. Authentication setup
The four different accounts need to be setup manually. All other resources while be managed with [Terraform](#3-terraform).

Once the accounts have been created, it is necessary to configure an AWS config file with the appropriate credentials. This configuration is crucial for local development and testing across the different accounts. To distinguish between the accounts, profiles are utilized. The configuration file, located at ~/.aws/config, is structured as follows:

```
[default]
aws_access_key_id=foo
aws_secret_access_key=bar
region=us-west-2

[profile dev]
...

[profile staging]
...

[profile prod]
...

[profile operations]
...
```
[Details on AWS credential-file](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)

## 2.1 Update Account-ID and repository references
Besides the `config` file there are a couple of other files, where we manually have to update our Account-ID's. All six files bellow need to be updated:
```bash
.
├── .github
│   └── workflows
│       └── on_tag.yml              #1
├── terraform
│   ├── main
│   │   └── environment
│   │       ├── dev.tfvars          #2
│   │       ├── staging.tfvars      #3
│   │       └── prod.tfvars         #4
│   └── operations
│        └── environment
│            └── operations.tfvars  #5
├── training_pipeline
│   └── profiles.conf               #6
└── ...
```

In the next step, it is essential to modify the reference to our repository for GitHub Actions authentication within the `main.tf` file located at `terraform/modules/openid_github_provider/`. In this file, you should replace the value "repo:ml6team/aws-promote-code:*" with the name of your repository. This adjustment allows GitHub to assume the required role and carry out continuous integration and deployment (CI/CD) actions seamlessly.

```YAML
data "aws_iam_policy_document" "assume_policy" {
  statement {
    ...
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:ml6team/aws-promote-code:*"] 
    }
    ...
  }
}
```

# 3. Terraform
In this project, we use Terraform to manage our infrastructure because it enables us to define infrastructure as code, ensure consistency, and easily scale our infrastructure. With Terraform, we can efficiently manage multiple environments, such as development, staging, and production, with consistent configurations and reproducible deployments, simplifying our infrastructure management across different stages of the project lifecycle.

## 3.1 Setup Terraform backend
The first step of setting up Terraform, is to create a remote backend for the Terraform-State on the `operations` account. This is done by running the following commands from the `terraform/backend` folder:
```
terraform init
terraform apply --var-file ../operations/environment/operations.tfvars
```

After this backend is created, we need to update the backend references inside our modules, as they can only be hardcoded. This means updating the `bucket` value in the following files:
```
.
└── terraform
    ├── main
    │   └── backend.tf
    └── operations
        └── backend.tf
```

Now you are ready to create the resources on the other accounts
## 3.2 Setup operations artifacts
Besides the Terraform-backend the operations account also hosts the different Docker-images in an Elastic-Container-Registry (ECR). Additionally the access rights for GitHub, which are needed to run our CI/CD, are created.

Create the resources by running the following command from the `terraform/operations` folder:
```
terraform init
terraform apply -var-file="environment/operations.tfvars"
```

## 3.3 Setup Terraform workspaces
To effectively distinguish between the three environments (dev, staging, prod), we will utilize **Terraform Workspaces**. This approach allows us to utilize a single Terraform configuration for all environments while maintaining separate Terraform states within the same backend. By leveraging Terraform Workspaces, we can seamlessly manage and deploy infrastructure across multiple environments with improved organization and ease of maintenance.
We create the three Terraform-workspaces inside the `terraform/main` folder by running:
```
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod
```
## 3.4 Deploy dev environment
To deploy our artifacts in the dev-environment we will activate the workspace and create our artifacts:
```
terraform workspace select dev
terraform init
terraform apply -var-file="environment/dev.tfvars" -var="enable_profile=true"
```
With the flag `-var-file` we specify which variables we want to use to create our artifacts. By setting the variable `enable_profile` as true, we tell Terraform to use the dev-profile we created in the [Authentication section](#2-authentication-setup). Because these Terraform files will also be used inside our [CI/CD-Pipeline](#4-cicd-pipeline-with-git-actions) the default setting is to ignore/disable the profile config, as it will not be available when run inside the pipeline. 

Your dev-environment is now ready for creating and running your training pipeline. For further details see the [Training-Pipeline README](./training_pipeline/README.md).

# 4. CI/CD Pipeline with Git actions
Once code changes have been implemented in the development environment, our workflow involves deploying these changes into the staging and production environments. For seamless CI/CD processes, we rely on GitHub Actions. These automated workflows are triggered to build and deploy any modifications made to the main branch initially in the `staging` environment and subsequently in the `production` environment. This ensures a streamlined and efficient deployment pipeline, enabling rapid and reliable software releases.

The complete CI/CD flow is visualized in the following diagram:
![CICD_diagram](/readme_images/CICD_diagram.png)

After you have reviewed a PR and decided to merge you feature-branch into your main-branch artifacts get automatically build. Next, as shown in the diagram add the `staging-tag` to your commit/merge on the `main` branch to trigger the deployment:
```
git tag staging
git push origin staging
```

Remember that after the initial creation of a tag, you need to add the `-f` flag to update the tag and trigger the deployment at later times:
```
git tag -f staging
git push -f origin staging
```
At this point tests can be run on your staging environment. After these test ran successfully you can add the `production-tag` to deploy to production:
```
git tag prod
git push origin prod
```