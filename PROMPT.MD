# PROMPT.MD

You are an expert Python developer tasked with building a complete, optimized ray tracing renderer from scratch in Python. Support advanced features: global illumination, subsurface scattering, volumetric effects, multi-threaded acceleration structures (e.g., BVH with Python's threading/multiprocessing). Include a scene description language parser, realistic PBR material models, and HDR image output. Ensure code is cross-platform, supporting ARM (Apple Silicon) and x86 architectures—use compatible libraries (e.g., numpy), avoid platform-specific code, and include checks for architecture in optimizations.

Use a RALPH loop: Read PROMPT.MD, Analyze current state, List to-do items, Plan next steps, Handle one chunk of work (code/tests/docs), then compact and loop back.

Maintain a to-do list in TODO.md, updating it incrementally. Start with basics (ray-sphere intersection) and build up: lighting, textures, reflections, refractions, advanced features, optimizations, bug fixes. Include multi-threading implementation and optimizations.

For every component and feature, write comprehensive tests: unit tests for functions/classes (e.g., intersection math, material shaders, multi-threading safety), integration tests for rendering pipelines, performance tests for optimizations (benchmark on ARM/x86 if possible, simulate x86 via env vars). Use pytest framework. Ensure tests cover edge cases, numerical stability, feature interactions, multi-threaded concurrency, and cross-platform compatibility (e.g., run on Apple Silicon, note for x86 testing). Run and fix tests in the loop before proceeding.

Structure project: main.py for entry, modules for core (ray.py, scene.py, materials.py, etc.), tests in tests/ directory. Version control changes: Maintain commits.md with change logs; at regular intervals (e.g., after major features/tests), prepare git commits—generate commands like 'git add .', 'git commit -m "description"', 'git push origin main' for the repo https://github.com/tbassignana/SpectraForge, and output them for user execution.

When compacting, always reread PROMPT.MD to stay on track. Aim for high-quality, efficient, cross-platform code.