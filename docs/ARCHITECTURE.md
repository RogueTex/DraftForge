# Architecture

## Components

- `apps/api/main.py`: Repair-agent API and provider integration.
- `apps/studio/*`: Browser-based debugging studio.

## Flow

1. User submits failing code and error trace.
2. `/analyze` produces severity and root-cause narrative.
3. `/repair` returns patch-oriented output plus test recommendations.
4. If provider is not configured, deterministic fallback responses keep demos reliable.
