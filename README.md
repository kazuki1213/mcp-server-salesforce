# mcp-server-salesforce MCP server

![CI](https://github.com/kazuki1213/mcp-server-salesforce/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.10-blue.svg)

A Model Context Protocol server implementation for interacting with Salesforce

## Components

### Resources

The server implements resources in two categories:

1. Notes storage system:
   - Custom note:// URI scheme for accessing individual notes
   - Each note resource has a name, description and text/plain mimetype

2. Salesforce objects:
   - Custom salesforce:// URI scheme for accessing Salesforce objects and records
   - Each object resource has a name, description and application/json mimetype

### Prompts

The server provides the following prompts:

- summarize-notes: Creates summaries of all stored notes
  - Optional "style" argument to control detail level (brief/detailed)
  - Generates prompt combining all current notes with style preference

- analyze-salesforce-data: Analyzes data from a Salesforce object
  - Required "object" argument to specify Salesforce object name (e.g., Account, Contact)
  - Optional "limit" argument to control maximum number of records (default: 10)
  - Retrieves and formats data for analysis

### Tools

The server implements the following tools:

1. Notes management:
   - add-note: Adds a new note to the server
     - Takes "name" and "content" as required string arguments
     - Updates server state and notifies clients of resource changes

2. Salesforce interactions:
   - salesforce-query: Execute a SOQL query against Salesforce
     - Takes "query" as a required string argument (valid SOQL query)
     - Returns query results as JSON

   - salesforce-create: Create a new record in Salesforce
     - Takes "object" (e.g., "Account") and "data" (field values) as required arguments
     - Returns the ID of the created record

   - salesforce-update: Update an existing Salesforce record
     - Takes "object", "id", and "data" as required arguments
     - Updates the specified record with new field values

   - salesforce-delete: Delete a Salesforce record
     - Takes "object" and "id" as required arguments
     - Deletes the specified record

## Configuration

To use the Salesforce functionality, you need to set up authentication credentials. 
The server supports environment variables or a .env file in the project root.

Required environment variables:
- SALESFORCE_USERNAME: Your Salesforce username (usually email)
- SALESFORCE_PASSWORD: Your Salesforce password
- SALESFORCE_SECURITY_TOKEN: Your Salesforce security token
- SALESFORCE_DOMAIN: (Optional) Salesforce login domain (default: "login")

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  ```
  "mcpServers": {
    "mcp-server-salesforce": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-server-salesforce",
        "run",
        "mcp-server-salesforce"
      ]
    }
  }
  ```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  ```
  "mcpServers": {
    "mcp-server-salesforce": {
      "command": "uvx",
      "args": [
        "mcp-server-salesforce"
      ]
    }
  }
  ```
</details>

## Development

### Building and Publishing

The project uses GitHub Actions for CI/CD:

- **CI Pipeline**: Automatically runs tests, type checking, and linting on every push and pull request
- **CD Pipeline**: Automatically builds and publishes to PyPI when a new version tag is pushed

To prepare a release:

1. Update the version in `pyproject.toml`
2. Create and push a tag: 
```bash
git tag v0.0.x
git push origin v0.0.x
```

This will trigger the automatic release process.

For manual builds:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).


You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp-server-salesforce run mcp-server-salesforce
```


Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.