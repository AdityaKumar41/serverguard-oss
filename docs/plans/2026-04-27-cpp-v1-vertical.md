# C++ v1 Vertical Slice Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build runnable C++ `sgd-cpp` and `sg-cpp` binaries for the ServerGuard v1 fixture path.

**Architecture:** Keep the implementation modular and header-light: config loading, validation, detection, event shaping, storage, daemon flow, and CLI rendering each live in separate files. The daemon processes configured logs once for the first contract slice, while storage writes the shared SQLite schema.

**Tech Stack:** C++20, CMake, system `libsqlite3.so.0` loaded dynamically, shared fixtures under `fixtures/`.

---

### Task 1: Build Skeleton And Failing Tests

**Files:**
- Create: `CMakeLists.txt`
- Create: `implementations/cpp/tests/config_validation_test.cpp`
- Create: `implementations/cpp/tests/detector_contract_test.cpp`
- Create: `implementations/cpp/tests/storage_contract_test.cpp`

**Steps:**
1. Add CMake targets for existing tests and new tests.
2. Add config validation tests for the shared fixture and an invalid empty instance ID.
3. Add detector test expecting one `security.ssh_bruteforce` event from the fixture.
4. Add storage test expecting a written event to be listed from SQLite.
5. Run CMake build and confirm the new tests fail because production code is missing.

### Task 2: Config Validation

**Files:**
- Create: `implementations/cpp/src/config_validate.hpp`
- Modify: `implementations/cpp/tests/config_validation_test.cpp`

**Steps:**
1. Implement required-field validation.
2. Implement uniqueness and detector-source validation.
3. Run config tests and existing config contract test.

### Task 3: Detector Event Output

**Files:**
- Create: `implementations/cpp/src/event.hpp`
- Create: `implementations/cpp/src/detector.hpp`
- Modify: `implementations/cpp/tests/detector_contract_test.cpp`

**Steps:**
1. Implement normalized `Event`.
2. Parse auth log lines with existing `ssh_auth.hpp`.
3. Apply threshold/window grouping by source IP.
4. Emit one security event matching fixture expectations.
5. Run detector and SSH parser tests.

### Task 4: SQLite Storage

**Files:**
- Create: `implementations/cpp/src/storage.hpp`
- Create: `implementations/cpp/src/storage.cpp`
- Modify: `implementations/cpp/tests/storage_contract_test.cpp`

**Steps:**
1. Open or create `<data_dir>/serverguard.db`.
2. Apply shared schema.
3. Insert normalized events.
4. List events in reverse chronological order.
5. Run storage tests.

### Task 5: Daemon And CLI

**Files:**
- Create: `implementations/cpp/src/daemon.cpp`
- Create: `implementations/cpp/src/cli.cpp`

**Steps:**
1. Implement `sgd-cpp --config <path>`.
2. Write daemon start and stop audit events.
3. Detect fixture SSH brute force and persist it.
4. Implement `sg-cpp status --config <path>`.
5. Implement `sg-cpp events --config <path>`.
6. Run binaries manually against the shared fixture.

### Task 6: Final Verification

**Files:**
- All C++ source and test files.

**Steps:**
1. Run `cmake -S . -B build`.
2. Run `cmake --build build`.
3. Run `ctest --test-dir build --output-on-failure`.
4. Run `./build/sgd-cpp --config fixtures/configs/basic.toml`.
5. Run `./build/sg-cpp status --config fixtures/configs/basic.toml`.
6. Run `./build/sg-cpp events --config fixtures/configs/basic.toml`.
