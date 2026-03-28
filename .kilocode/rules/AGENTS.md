# Agent Context

## System Description

This project is an API-driven backend service for dynamic collage generation.

The service accepts:

- **N source images**
- **layout and rendering metadata**

The metadata may include:

- target dimensions
- image coordinates
- z-index / stacking order
- margins and padding
- alignment constraints
- other composition parameters required for rendering

Using these inputs, the system performs server-side image composition and produces a final collage image as output.

## Implementation

The system is implemented in **Python** with the following core libraries:

- **FastAPI** for HTTP API handling
- **Pillow (PIL)** for image decoding, transformation, composition, and rendering

## Core Workflow

1. Receive request with image assets and layout metadata
2. Validate and normalize input parameters
3. Load and preprocess source images
4. Apply placement and composition rules
5. Render the final collage
6. Return the generated image to the client

## Non-Functional Requirements

- low-latency collage generation
- predictable behavior under concurrent load
- scalability for up to **100 concurrent requests**
- efficient memory and CPU utilization during image processing

## Operational Goal

The service is intended for high-speed collage generation in environments where multiple users may submit requests at the same time. The expected load profile assumes up to **100 concurrent users**, so the implementation should prioritize throughput, resource efficiency, and request stability.
