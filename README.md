# stone-burner

[![Build Status](https://travis-ci.org/kkvesper/stone-burner.svg?branch=master)](https://travis-ci.org/kkvesper/stone-burner)

Wrapper over `terraform` which adds a configuration layer and state splitting between
projects and/or environments, among other features.

## Requirements

* [Terraform](https://www.terraform.io/) v0.11 or higher
* Python 3.6

## Install

```bash
pip install --upgrade stone-burner
```

## Usage

```bash
stone-burner --help
stone-burner <command> --help
```

*Note: The first time using terraform you will have to run `stone-burner install` to initialize
your projects.

### Example

```bash
stone-burner plan project_1               # plan all components from project_1
stone-burner plan project_1 -c c1         # plan only c1
stone-burner plan project_1 -c c1 -c c2   # plan only c1 and c2
stone-burner plan project_1 -xc c3 -xc c4 # plan all except c3 and c4
```

_Note:_ You can plan one project only if the projects it depends on have been applied.

#### Passing extra parameters to terraform

If you want to send extra parameters to `terraform` (like for example, the `-target`
option), make sure to use `--` to avoid `stone-burner` trying to parse those options.
For example:

```bash
stone-burner apply -e production project_1 -c c1 -- -target=some_resource.address
```

### Install provider plugins

If you are using provider plugins in your configuration files, you will need to first install them
in order to start working with terraform.

`stone-burner` installs all the plugins under `~/.stoneburner/plugins` in order to save space disk and
avoid re-downloading same plugins that are used in your different project/components.

There are 2 ways of installing terraform provider plugins:

- Discover and install from your configuration files:
    ```bash
    stone-burner install -p project_1 -c c1 -c c2
    ```

- Install plugins and versions manually:
    ```bash
    stone-burner install template@1.0.0 aws@1.5.0 kubernetes@1.0.1
    ```

## Configuration

The way projects are configured is via the `--config` flag (`config.yml` by default).
In this file, you can define projects by combining individual components and variables. For example:

```yaml
projects:
  project_1:
    - database            # projects/project_1/database + variables/<environment>/project_1/database
    - app                 # projects/project_1/app + variables/<environment>/project_1/app
  project_2:
    - database:
      - database_1        # projects/project_2/database + variables/<environment>/project_2/database_1
      - database_2        # projects/project_2/database + variables/<environment>/project_2/database_2
    - app:
      - app_1             # projects/project_2/app + variables/<environment>/project_2/app_1
      - app_2             # projects/project_2/app + variables/<environment>/project_2/app_2
```

So, there are 3 different key/values here:

- Top level keys refer to **projects**.
- List elements under the project can be defined in 2 ways:
  - As a string, a `component` and `variables` with the same project and
  component name will be used.
  - As a dictionary, the key will refer to a *generic component* or *component type*. The list items under
  this key will all use the same `component` (terraform configuration) using different variables.

### Environments

You must define your environment details in your configuration file before you can
use your `-e` or `--environment` flag. For example:

```yaml
environments:
  - name: production
    aws_profile: my-production-profile
    states_bucket: terraform-states-production

  - name: staging
    aws_profile: my-staging-profile
    states_bucket: terraform-states-staging
    default: true
```
