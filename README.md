# kubectl-application-shell

A kubectl plugin that creates safe debug pods from existing Kubernetes deployments.

## Description

This kubectl plugin solves a common problem in Kubernetes debugging:

> When you need to run one-off tasks (SQL queries, file inspections, environment debugging), the traditional approach is `kubectl exec` into a running pod. However, this can cause issues if your command crashes the pod, potentially impacting production traffic.

**kubectl-application-shell** provides a safer alternative by creating isolated debug pods that inherit the configuration from your existing deployment (image, environment variables, volumes, resource limits) without affecting running services.

## Features

- 🚀 **Safe Debugging**: Creates isolated pods that don't impact production
- 🔄 **Auto-Configuration**: Inherits image, env vars, volumes, and resources from target deployment
- 🔗 **Session Management**: Resume disconnected sessions, list active sessions, manage multiple debugging sessions
- 🛡️ **Security Options**: Service accounts, user contexts, privileged mode, network policies
- 💾 **Storage Access**: Mount PVCs for persistent data debugging
- 📝 **Session Logging**: Record debugging sessions for later analysis
- ⚡ **Resource Control**: Override CPU/memory limits for specific debugging needs
- 🎯 **Node Targeting**: Schedule on specific nodes for hardware-specific debugging

## Prerequisites

- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) (automatically downloaded if needed)
- Python 3.9+

## Installation

### Using pipenv (Development)
```bash
pipenv install
pipenv shell
```

### Using pip (Production)
```bash
pip install -e .
```

## Quick Start

```bash
# 1. Create a debug session from a deployment
kubeas production api-server --run

# 2. List active sessions (from another terminal)
kubeas list-sessions

# 3. Resume the session later
kubeas resume-session debug-api-server-abc123 -n production --run

# 4. Clean up when done
kubeas terminate-session debug-api-server-abc123 -n production
```

## Basic Usage

```bash
# Create debug pod from deployment
kubeas <namespace> <deployment>

# Run immediately without showing command
kubeas <namespace> <deployment> --run

# Use custom shell/command
kubeas <namespace> <deployment> /bin/zsh

# Pass arguments to the command
kubeas <namespace> <deployment> python3 script.py --verbose
```

## Advanced Options

### Authentication & Authorization
```bash
# Use specific service account for RBAC debugging
kubeas <namespace> <deployment> --service-account debug-sa

# Run as specific user ID
kubeas <namespace> <deployment> --run-as-user 1000
```

### Environment & Runtime
```bash
# Override environment variables
kubeas <namespace> <deployment> --env DEBUG=true --env LOG_LEVEL=debug

# Set working directory
kubeas <namespace> <deployment> --workdir /app/scripts

# Custom timeout for pod startup
kubeas <namespace> <deployment> --timeout 10m
```

### Resource Management
```bash
# Override resource limits
kubeas <namespace> <deployment> --cpu-limit 2 --memory-limit 4Gi

# Set specific resource requests
kubeas <namespace> <deployment> --cpu-request 500m --memory-request 1Gi
```

### Storage & Networking
```bash
# Mount persistent volume
kubeas <namespace> <deployment> --mount-pvc data-pvc

# Use host network for network debugging
kubeas <namespace> <deployment> --host-network

# Target specific nodes
kubeas <namespace> <deployment> --node-selector kubernetes.io/arch=amd64
```

### Security & Debugging
```bash
# Run in privileged mode for system debugging
kubeas <namespace> <deployment> --privileged

# Create network policies for isolation
kubeas <namespace> <deployment> --network-policy block-all-egress

# Allow specific ports through network policy
kubeas <namespace> <deployment> --network-policy allow-port --network-port 8080
```

### Session Management
```bash
# Log entire session to file
kubeas <namespace> <deployment> --session-log debug-session.log

# Non-interactive mode for automation
kubeas <namespace> <deployment> --no-tty

# List active debug sessions
kubeas list-sessions
kubeas list-sessions -n production

# Resume an existing session
kubeas resume-session debug-api-abc123 -n production

# Terminate a session
kubeas terminate-session debug-api-abc123 -n production
```

## Common Use Cases

### Database Debugging
```bash
# Debug database connectivity with mounted data
kubeas production api-server --mount-pvc postgres-data --env DEBUG_DB=true
```

### Network Troubleshooting
```bash
# Debug network issues with host network access
kubeas production web-app --host-network --privileged
```

### Performance Analysis
```bash
# Run with higher resources for performance testing
kubeas staging api --cpu-limit 4 --memory-limit 8Gi --session-log perf-test.log
```

### RBAC Testing
```bash
# Test with different service account permissions
kubeas production worker --service-account restricted-sa --no-tty
```

### Session Management Workflow
```bash
# 1. Start a debug session (persists after disconnection)
kubeas production api-server

# 2. List active sessions to see what's running
kubeas list-sessions

# 3. Resume a session from another terminal/machine
kubeas resume-session debug-api-server-abc123 -n production --run

# 4. Clean up when done
kubeas terminate-session debug-api-server-abc123 -n production
```

## How It Works

1. **Deployment Inspection**: Queries the target deployment to extract configuration
2. **Kubectl Download**: Automatically downloads cluster-compatible kubectl binary
3. **Pod Generation**: Creates pod spec inheriting deployment configuration with session tracking labels
4. **Resource Creation**: Applies any network policies or additional resources
5. **Session Management**: Launches interactive shell with persistent session capability
6. **Session Tracking**: Uses pod labels with user identifiers for session ownership and management
7. **Cleanup**: NetworkPolicies auto-cleanup; pods persist for resumption until manually terminated

## Advanced Features

### Network Policies
When using `--network-policy`, the tool creates Kubernetes NetworkPolicy resources:
- `block-all-ingress`: Deny incoming traffic
- `block-all-egress`: Deny outgoing traffic  
- `block-all`: Deny all traffic
- `allow-port`: Allow specific port (requires `--network-port`)
- `allow-port-range`: Allow port range (requires `--network-port-range`)

### Session Management
- **Persistent Sessions**: Debug pods persist after terminal disconnection for later resumption
- **User Isolation**: Each user can only manage their own sessions (based on system username)
- **Cross-Platform**: Session state stored in Kubernetes labels, works from any machine
- **Session Discovery**: `list-sessions` shows all active debug sessions with metadata

### Automatic Cleanup
- **NetworkPolicies**: Automatically deleted when sessions end
- **Debug Pods**: Persist for resumption; use `terminate-session` for manual cleanup
- **Cleanup Reminders**: Tool shows cleanup commands when not auto-running

## Command Reference

### Main Commands
```bash
kubeas <namespace> <deployment> [command] [options]    # Create debug session
kubeas list-sessions [-n namespace]                     # List active sessions  
kubeas resume-session <name> -n <namespace> [options]   # Resume existing session
kubeas terminate-session <name> -n <namespace>          # Terminate session
```

### Common Options
```bash
--run                    # Execute immediately
--context <name>         # Use specific kubeconfig context
--service-account <sa>   # Use specific service account
--env KEY=VALUE          # Set environment variables
--cpu-limit <limit>      # Override CPU limit
--memory-limit <limit>   # Override memory limit
--mount-pvc <pvc>        # Mount persistent volume
--session-log <file>     # Log session to file
--privileged             # Run in privileged mode
--host-network           # Use host network
--no-tty                 # Non-interactive mode
```

## Troubleshooting

### Common Issues
- **Permission Denied**: Use `--service-account` with appropriate RBAC
- **Image Pull Errors**: Verify the deployment's image is accessible
- **Network Issues**: Try `--host-network` for network debugging
- **Resource Constraints**: Use custom `--cpu-limit` and `--memory-limit`
- **Session Not Found**: Check namespace with `kubeas list-sessions`
- **Cannot Resume Session**: Verify you own the session (sessions are user-isolated)

### Session Management Issues
```bash
# Check if sessions exist
kubeas list-sessions

# Verify session ownership (only your username sessions are manageable)
kubeas list-sessions -n <namespace>

# Force cleanup if needed (requires kubectl access)
kubectl delete pod <session-name> -n <namespace>
```

### Getting Help
```bash
kubeas --help                           # Main command help
kubeas list-sessions --help             # Session listing help
kubeas resume-session --help            # Resume command help
kubeas terminate-session --help         # Terminate command help
```

## Contributing

### Development Setup
```bash
git clone <repository>
cd kubectl-application-shell
pipenv install --dev
pipenv shell
```

### Testing
```bash
# Test against a real cluster
kubeas test-namespace test-deployment --run

# Test session management
kubeas list-sessions
```

### Architecture
This project uses:
- **Typer** for CLI interface with multiple commands
- **Rich** for colored output and tables
- **Kubernetes Python Client** for API interactions
- **Pipenv** for dependency management
- **Pod Labels** for session tracking and user isolation

### Key Files
- `src/kubectl_application_shell/app.py` - Main debug session creation logic
- `src/kubectl_application_shell/cli.py` - CLI commands and interface
- `src/kubectl_application_shell/func.py` - Kubernetes API functions and session management
- `src/kubectl_application_shell/console.py` - Rich console instance

### Adding Features
1. Add new CLI options to `app.py` main function
2. Update pod spec generation logic
3. Add corresponding functions to `func.py` if needed
4. Update documentation in README.md and CLAUDE.md

## License

See project license file.
