<div style="display: flex; justify-content: center;">
  <img src="readme_images/ML6_black_round.png" alt="Image 1" width="40px" style="margin-right: 10px;">
  <img src="https://skillicons.dev/icons?i=aws" alt="Image 2" width="40px">
</div>
<br>
<h1 align="center">AWS MLOps Artifact by ML6 </h1>
In this repository ML6 presents a template for MLOps projects in AWS. Here we want to show the way of working at ML6, where we promote code thru different environments instead of models. This has multiple benefits:
- Model and supporting code such as inference pipelines can follow the same staging pattern.
- Training code is reviewed and retraining can be automated in production.
- Staging of time series pipeline can be unified with regression/classification.
- Production data access in development environment is not needed.

# 1. Project structure
This project has 3 different environments and a total of 4 AWS accounts:
- 3 environments / accounts: development, staging, production
- 1 operations account which runs CI/CD and hosts artifacts that need to be promoted across environments

# 2. Authentication setup
This project has 4 different accounts that need to be setup manually. All other resources while be managed with Terraform.

After creating the accounts, we need to configure a AWS config-file with the credentials. This is needed for local developing und testing on the different accounts. To differentiate between the accounts we use so-called profiles. The config-file with these profiles is located in `~/.aws/config` and looks like this:

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
Besides the `config` file there are a couple of other files, where we manually have to update our account-ids:
```bash
.
├── .github
│   └── workflows
│       └── on_tag.yml
├── terraform
│   ├── main
│   │   └── environment
│   │       ├── dev.tfvars
│   │       ├── staging.tfvars
│   │       └── prod.tfvars
│   └── operations
│        └── environment
│            └── operations.tfvars
├── training_pipeline
│   └── profiles.conf
└── ...
```

The next step is to update the reference to our repository for the GitHub-actions authentication in the file `terraform/modules/openid_github_provider/main.tf`. Here you need to change the value *"repo:ml6team/aws-promote-code:*"* to the name of your repo, so GitHub can assume the needed role:

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
This rule ensures that only GitHub actions run from your repo can assume this role.

# 3. Terraform

## 3.1 Setup Terraform backend
The first step of setting up Terraform, is to create a remote backend for the Terraform-State on the `operations` account. This is done by running the following command from the `terraform/backend` folder:
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
Besides the Terraform-backend the operations account also hosts the different Docker-images in an Elastic-Container-Registry (ECR). Additionally the access rights for GitHub, which are needed to run our CICD, are created.

Create the resources by running the following command from the `terraform/operations` folder:
```
terraform init
terraform apply -var-file="environment/operations.tfvars"
```

## 3.3 Setup Terraform workspaces
To differentiate between the three environments (dev, staging, prod) we will be working with **Terraform-Workspaces**. This means we can use the same Terraform configuration for all three environments and also have the individual Terraform-States in the same backend. 
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
With the flag `-var-file` we specify which variables we want to use to create our artifacts. By setting the variable `enable_profile` as true, we tell Terraform to use the dev-profile we created in the [Authentication section](#2-authentication-setup). Because these Terraform files will also be used inside our [CICD-Pipeline](#4-cicd-pipeline-with-git-actions) the default setting is to ignore/disable the profile config, as it will not be available when run inside the pipeline. 

Your dev-environment is now ready for creating and running your training pipeline. For further details see the [Training-Pipeline README](./training_pipeline/README.md).

# 4. CICD Pipeline with Git actions
After we have made code changes in the dev-environment, we want to deploy these changes into staging and production. For Continues Integration and Continues Deployment (CICD) we are using GitHub actions. They automatically build and deploy all changes which are made to the `main` branch in the **staging** environment and after that in the **production** environment.

To trigger the deployment add the tag to you current commit/merge on the `main` branch. In this case the `staging` tag:
```
git tag staging
git push origin staging
```

Remember that after the initial creation of a tag, you need to add the `-f` flag to update the tag and trigger the deployment again:
```
git tag -f staging
git push -f origin staging
```

For deployment to `production` simply change the tag name.