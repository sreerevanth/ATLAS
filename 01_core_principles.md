# ATLAS Core Principles

> **Historical material — not current validation evidence.** Retained for design
> context, contributor attribution and provenance. Phase labels, figures and
> capability statements below are not current ATLAS claims. See the
> [current evidence and historical-material guide](docs/HISTORICAL_MATERIAL.md).

These principles serve as the constitution of ATLAS. Every architectural, theoretical, and engineering decision must be checked against them. If a feature or idea violates a core principle, it does not go into ATLAS—no matter how clever or convenient it may seem.

### Principle 1: Data is sovereign.
**Raw data never leaves its organization.**
Data remains at rest in its origin environment. The underlying text, documents, images, and unencrypted embeddings must never be transmitted across organizational boundaries.

### Principle 2: Only computation moves.
**Never datasets.**
Instead of aggregating data into a centralized cluster for processing, ATLAS brings the processing directly to the distributed data. Code travels; data does not.

### Principle 3: Every computation must be temporary.
**No persistent execution.**
When computation moves to an organization, its execution environment (e.g., Ephemeral WASM Agents) must be strictly scoped, sandboxed, and completely destroyed after yielding the necessary inference or operation. There are no lingering agents.

### Principle 4: Topology decides where to search.
**AI decides what to infer.**
Routing and discovery across the distributed network are fundamentally geometric. We use the topological structure (the shape) of the data to localize regions of interest. Only after this geometric navigation isolates the right region does an AI agent deploy to perform inference.

### Principle 5: Organizations never reveal their internal structure.
**Only privacy-preserving topology fingerprints.**
An organization's internal schema, data distribution, and graph exactness are private. External actors only see aggregate, privacy-preserving topological representations (e.g., Persistence Landscapes, Locality Sensitive Hashes) that summarize shape without exposing sensitive points.

### Principle 6: Every response should leak the minimum possible information.
Information transmitted back after an execution must strictly adhere to the principle of least privilege. Responses are synthesized to contain only the answer to the localized query, stripping away any metadata, context, or auxiliary data that is not absolutely required to fulfill the task.
