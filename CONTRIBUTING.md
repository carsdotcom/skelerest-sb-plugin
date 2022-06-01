Contributing
---

If you would like to get involved and contribute to this project, please read
through the [Code of Conduct](CODE_OF_CONDUCT.md) first. Then, read through 
this document to understand Process Guidelines, and the general Scope of the project.

---

## Maintainers

 * Sean Shookman | Data Scientist | sshookman@cars.com

## Project Scope

The purpose of this project is to create a plugin for Skelebot that allows for REST requests to be
configured, parameterized, and executed via the Skelebot CLI.

### Configured Requests

The REST requests are configured through the `components` section of the Skelebot.yaml config file.
This allows for the user to specify any number of GET, POST, PUT, or DELETE requests as they want.
Requests must provide necessary details for the API endpoint and the REST method. A name must also
be provided in order to generate the CLI command. Other optional values for the request can also be
specified in the config, such as query parameters, header parameters, and a POST/PUT body.

### Parameterized Requests

The configured requests can be made more flexible through the use of variables. Variables allow
certain parts of the request to be altered when the CLI command is executed by specifying the
corresponding variable name and value as a parameter to the Skelebot command. All of the variables
configured in the request are made available to the Skelebot CLI automatically by plugin.

### Execution

Each request is interpreted by the plugin and a new Skelebot command is created in the CLI with
which it can be executed. These commands can be viewed through the `--help` parameter in Skelebot
CLI just like any other command. The parameterized variables of the request also show up as
paramters in the `--help` output of the request commands themselves.

## Guidelines for Contributing

### Read The Docs

More information about the project can be found in the [README](README.md). Make sure you have
gone over the documentation before starting on any contributions to the project.

### Announce Your Work

All issues (bugs, features, and tasks) are tracked in GitHub [Issues](https://github.com/carsdotcom/skelerest/issues).

If you would like to request a new feature or raise a bug, you can use the appropriate issues
templates to do so. Before opening a feature request, be sure it fits into the 'Project Scope'
that is defined above.

If there is a reported issue that you would like to work on, comment on the issue directly
and discuss with the project maintainers the best approach before starting to code.

Letting others know what you are working on helps prevent contributors from stepping on each
others' toes, and helps the maintainers to plan and organize the project.

### Fork the Repo

When you are ready to start working, fork this repository where you can begin coding.

### Maintain Tests, Comments, and Docs

Ensure all existing test cases are passing and any new test cases have been added to cover the
functionality that you introduce in your code.

Make sure code is commented well so that others can understand it fairly quickly. There is no
need to write paragraphs of explanation, but high level descriptions for functions, large segments
of code, or complicated code is very helpful. We recommend adhering the docstring format that is
already in use in the codebase.

If you are adding new functionality or modifying existing functionality, make sure the documentation
is updated accordingly.

### Open a Pull Request

Once you have made your changes in your forked repository (and all tests are passing) you
can open a Pull Request to get your code reviewed by the maintainers. Iterate your changes as the
project maintainers comment on your code. Once the maintainers have agreed that the code is ready,
it will be merged into the master branch of this repository and become a part of the Skelerest
plugin.

Thank You!
