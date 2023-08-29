# Contributing

Thank you for helping to improve `mediawiki-client-tools`. We're glad you're here!

This document is an ongoing process for establishing and refining a set of best practices. Most of the things here are flexible or open to further iteration.

## Reporting Issues

If you find anything amiss, you can report it using [GitHub Issues](https://github.com/mediawiki-client-tools/mediawiki-dump-generator/issues). The template is there to help you communicate clearly. It's okay if you change it to meet your needs, though, as it is merely a suggested baseline.

For anything that doesn't fit, you can open a less formal conversation in [GitHub Discussions](https://github.com/orgs/mediawiki-client-tools/discussions) and feel free to tag any of the members of our GitHub organization.

If you wish to keep your concerns private, you can contact the organization administrator directly via email at [mediawiki-client-tools@elsiehupp.com](mailto:mediawiki-client-tools@elsiehupp.com) or on Matrix at [@elsiehupp:beeper.com](https://matrix.to/#/@elsiehupp:beeper.com).

## Tools

GitHub is a fancy frontend built on top of [Git](https://git-scm.com/) source control, and there is an official [Git Book](https://git-scm.com/book) you can read, skim, or search to familiarize yourself with Git, in particular.

GitHub also has its own [introduction to Git](https://docs.github.com/en/get-started/using-git) as part of its [Getting Started Guide](https://docs.github.com/get-started), as well as much more extensive [documentation](https://docs.github.com) on how to use the site.

Git can be counterintuitive, and [GitHub Desktop](https://desktop.github.com/) on macOS and Windows can be a friendlier and more approachable interface for using it.

[Visual Studio Code](https://code.visualstudio.com/) ("VSCode") is a convenient development environment that integrates with GitHub. You can use any environment you'd like, though this is among the easiest.

VSCode has [a guide to source control](https://code.visualstudio.com/docs/sourcecontrol/overview), and it has [an extension for working with GitHub](https://marketplace.visualstudio.com/items?itemName=GitHub.vscode-pull-request-github) which you may also find convenient.

In addition to the tools listed in the basic installation instructions in the main [README](./README.md), you can install [`pre-commit`](https://pre-commit.com/) in order to check and verify your work before submitting it.

## Contributing Code

`mediawiki-client-tools` has implemented a basic code-review and continuous-integration process which we are working to improve. With the following steps you can help us incorporate your work into our common codebase.

### 1. Fork the repository if you don't have write access

You can do so [here](https://github.com/mediawiki-client-tools/mediawiki-dump-generator/fork).

### 2. Clone the repository (or your fork) if you'd like to work on it locally (such as in VS Code)

This is particularly important if you are contributing executible code, so that you can use "code intelligence" and test your work. You can clone the repository using the big green **Code** button on the homepage of the repository (or your fork).

Alternately, you can [create a codespace](https://github.com/mediawiki-client-tools/mediawiki-dump-generator/codespaces) (also from the big green **Code** button), though we have yet to set up a consistent development container.

### 3. Create a new branch for the changes you'd like to make

It is helpful if you use a separate branch for each task, in order to keep your Pull Requests narrowly focused so that they are easier to review.

See the GitHub Desktop or VSCode documentation for how to create a new branch with either of these tools. If you are using GitHub's web-based editor, you will be prompted to do so when you click the big green **Commit changes...** button in the upper right.

While it isn't the end of the world if you use the default suggested branch name, it can be helpful if you use something slightly more memorable like `fix-infinite-loop-bug` or `update-contribution-guidelines` ;-) to make it easier for code reviewers to check out your changes.

### 4. Commit your changes

While there isn't really the space here to explain the technical process of Git commits, it can be helpful if you follow [some best practices](https://cbea.ms/git-commit/) with your commit messages. You don't have to do so up front, but we ask that you follow these best practices for writing a commit message when you open a pull request.

### 5. Open a Pull Request

> **Note:** If you use a single commit when opening a Pull Request, GitHub will automatically use the commit message to populate the text fields.

While we don't currently have a Pull Request template (as we do with Issues), it helps if you do the following (in no particular order):

* Please keep your Pull Requests as narrowly focused as possible in order to facilitate code review. If you have multiple unrelated commits, it would probably work better if you manage each one on a separate branch and as separate Pull Requests.
* If you don't want to squash your commits on merge, you should probably open them as separate Pull Requests instead.
* If your Pull Request isn't solving an Issue, you may consider opening one first (and using the template there to explain your rationale). You can feel free to explain if you are planning on solving the Issue yourself.
* If your Pull Request will help close an issue, please link to it in the text.
* It is helpful if you tick the box reading "allow maintainers to edit" so that we can collaborate directly on the code with you.
* If you haven't previously contributed, please add your name to the "Contributors" section at the bottom of the main [README](./README.md).

## Reviewing Code

If you have made a helpful contribution in the past, we may invite you to become a member of the `mediawiki-client-tools` GitHub organization.

In addition to allowing you to create and edit branches directly on this repository, being a member of the organization will allow you to review and approve other people's Pull Requests.

While there are certain hardcoded prerequisites in place before a Pull Request can be merged, you should also use your discretion and invite other contibutors to discuss if you think any changes may be controversial or disruptive.

---

Thank you again for your help!
