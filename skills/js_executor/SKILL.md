---
name: js_executor
description: Execute JavaScript code using Node.js vm
allowed-tools: [js_evaluator]
model: qwen-plus
---

This skill allows executing JavaScript code for code analysis and testing purposes.

## Capabilities

- Execute JavaScript code in a Node.js `vm` sandbox
- Pass custom context variables
- Retrieve execution results
- Support for modern ES6+ syntax via Node.js

## Usage

The skill accepts the following parameters:
- `code` (required): JavaScript code to execute
- `context` (optional): Dictionary of variables to initialize the execution context

## Example

```javascript
// Boolean logic
const a = true;
const b = false;
a && b; // return false
```

## Notes

- Timeout is set to 5 seconds
