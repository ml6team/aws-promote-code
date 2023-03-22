# Terraform backend infrastructure

This directory defines the infrastructure for the backend where Terraform stores its state. The
state of the backend cannot be stored in the backend itself, which is why it is separated from the
main Terraform configuration.

The state of the backend configuration is instead stored locally and can be tracked in git. This is
an acceptable solution since the backend should rarely be changed.

This means that you now have 2 separate Terraform configuration and states.

- The backend configuration: for which the state is stored locally and tracked in git.
- The main configuration: for which the state is stored remotely in the backend.

## Deployment

To deploy, run the following steps from this directory:

```commandline
terraform init
terraform apply --var-file ../environment/project.tfvars
```

## Tracking the state

The state of this infrastructure needs to be tracked separately by adding the
`terraform.tfstate` file to git. Next to the `main.tf` file and `README.md`, all other files can be
ignored. A `.gitignore` file is automatically generated to handle this.
