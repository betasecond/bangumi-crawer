# Specification: CLI Usage and Commands

This document specifies the design and functionality of the command-line interface (CLI) for the `bangumi-crawer` project. The CLI will provide a user-friendly way to interact with the Bangumi API through the generated SDK.

## 1. Objective

The main objective is to create a powerful and intuitive CLI that exposes the key functionalities of the Bangumi API. The CLI should be easy to use, self-documenting, and consistent with the structure of the API.

## 2. CLI Structure

The CLI will be built using `typer` and will follow a nested command structure that mirrors the API's service-based organization.

The base command will be `bangumi-crawer`.

```
bangumi-crawer <service> <command> [OPTIONS]
```

-   **`<service>`:** Represents a group of related API endpoints (e.g., `users`, `collections`). This will correspond to the service classes in the generated SDK.
-   **`<command>`:** Represents a specific API operation (e.g., `get-collections`, `update-status`).

## 3. Core Commands

### `init`

-   **Usage:** `bangumi-crawer init`
-   **Functionality:** As already implemented, this command will download the `bangumi.json` OpenAPI specification and trigger the SDK generation process. This will be the first command a user runs to set up the tool.

### Service-Based Commands

For each service in the generated SDK, a corresponding subcommand will be created. For example:

-   `bangumi-crawer users`
-   `bangumi-crawer collections`

Each of these service commands will have its own set of subcommands that map to the API operations.

#### Example: `users` service

-   **`get-by-username`:**
    -   **Usage:** `bangumi-crawer users get-by-username <username>`
    -   **Functionality:** Fetches public information for a specific user.
-   **`get-collections`:**
    -   **Usage:** `bangumi-crawer users get-collections <username> --type <type>`
    -   **Functionality:** Retrieves the collections of a specific user, with an optional filter for collection type (e.g., `watching`, `completed`).

## 4. Implementation Details

-   **Dynamic Command Generation:** Instead of manually defining every command, we will explore dynamically generating the `typer` CLI commands based on the structure of the generated SDK. This will ensure that the CLI always stays in sync with the API.
-   **Authentication:** The CLI will automatically read the `BANGUMI_ACCESS_TOKEN` from the `.env` file and use it to initialize the SDK client. The user will not need to pass the token manually for each command.
-   **Output Formatting:** The output of each command will be formatted for readability. For simple data, plain text will be used. For complex objects (e.g., JSON responses), we will use the `rich` library to pretty-print the output with syntax highlighting.
-   **Help and Documentation:** `typer` provides automatic help generation. The docstrings from the generated SDK will be used to populate the help messages for each command, making the CLI self-documenting.

## 5. Error Handling

-   The CLI will handle API errors gracefully. If the API returns an error (e.g., 404 Not Found, 401 Unauthorized), the CLI will display a clear, user-friendly error message instead of a stack trace.
-   Input validation errors (e.g., missing required arguments) will also be handled cleanly by `typer`. 