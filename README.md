# ServerGuard OSS

ServerGuard is a local-first server monitoring research project. The v1 slice compares Go, Rust, and C++ implementations against one shared specification, fixture set, and contract behavior.

Current implementation status:

- Shared v1 specs and fixtures are present.
- The C++ vertical slice builds `sgd-cpp` and `sg-cpp`.
- The C++ daemon loads TOML config, scans the auth log fixture, detects SSH brute force, and stores normalized events in SQLite.
- The C++ CLI supports `status` and `events`.

## Build And Test

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

## Run The C++ Slice

```bash
rm -rf tmp/basic-data
./build/sgd-cpp --config fixtures/configs/basic.toml
./build/sg-cpp status --config fixtures/configs/basic.toml
./build/sg-cpp events --config fixtures/configs/basic.toml
```

The fixture should produce one `security.ssh_bruteforce` event for `203.0.113.10`, plus daemon start/stop audit events.

