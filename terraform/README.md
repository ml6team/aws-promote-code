# Terraform by Nimbus

Nimbus can generate [Terraform](https://www.terraform.io/) configuration to help you set up the 
necessary infrastructure at the start of your project and for each generated component.

### Directory structure

The Terraform directory consists of 4 subdirectories:

- **backend**  
  Contains the configuration for the Terraform backend which stores the state of the main 
  configuration. The backend configuration and state are separated to prevent chicken-and-egg 
  issues. For more info, check the [README.md](./backend/README.md) in the subdirectory.
- **environment**  
  Contains the `.tfvars` files with the global variables for the project. Originally, this 
  directory contains a single `project.tfvars` file, but when moving to multiple environments, 
  you'll want separate `.tfvars` files per environment. You can pass these files to any Terraform 
  command using the `--var-file` argument
- **main**  
  The main Terraform configuration of the project. 
- **modules**  
  [Modules](https://developer.hashicorp.com/terraform/language/modules) that can be shared across 
  configurations or just be used to package logical resources together.

### Terraform version

The supported terraform version can be found in [versions.tf](./versions.tf).
We recommend [tfenv](https://github.com/tfutils/tfenv) to manage different
Terraform versions on your machine.

### Remote state

By default, Terraform stores state locally in a file named `terraform.tfstate`. When working with
Terraform in a team, use of a local file makes Terraform usage complicated because each user must
make sure they always have the latest state data before running Terraform and make sure that nobody
else runs Terraform at the same time. To solve this Terraform allows to store the state remotely.
In general, storing the state remotely has much more advantages than just working in a team. It 
also increases reliability in terms of backups, keeps your infrastructure secure by making the 
process of applying the Terraform updates stable and secure, and facilitates the use of Terraform 
in automated pipelines. At ML6 we believe using the remote state is the way of working with Terraform.

Nimbus setup enforces the remote state by generating `backend.tf` file, which makes sure Terraform 
automatically writes the state data to the cloud. The `backend` subdirectory contains the 
configuration of this backend infrastructure.

### Multiple environments

#### Terraform variables

To keep your terraform commands nice and short we recommend one file per environment.
If you want to start using multiple environments, duplicate the `project.tfvars` file and rename appropriately.

```
.                                           .
├── terraform/                              ├── terraform/
|     ├── environment/                      |     ├── environment/
|         └── project.tfvars  ----->        |         ├── sbx.tfvars
|                               └-->        |         └── dev.tfvars
|     ├── modules/                          |     ├── modules/
|     └── main.tf                           |     └── main.tf
└── ...                                     └── ...
```

You can now change variables per environment. For example you could change the project of your dev environment.

To execute terraform commands you will now provide one of the tfvars files

```bash
terraform plan --var-file environment/sbx.tfvars
```

#### Terraform workspaces

When you create resources with terraform they are recorded in a terraform state.
To have multiple environments running at the same time you will have to create multiple states,
one for each environment. To do this use the `terraform workspace` command.

### Component documentation

For more detailed documentation about certain components, check the [Nimbus documentation](https://nimbus-documentation-dot-ml6-internal-tools.uc.r.appspot.com/).