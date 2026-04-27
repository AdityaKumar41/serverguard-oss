cmake_minimum_required(VERSION 3.20)
project(serverguard_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_compile_options(-Wall -Wextra -Wpedantic)

enable_testing()

add_library(serverguard_storage implementations/cpp/src/storage.cpp)
target_include_directories(serverguard_storage PUBLIC implementations/cpp/src)
target_link_libraries(serverguard_storage PRIVATE dl)

add_executable(sgd-cpp implementations/cpp/src/daemon.cpp)
target_include_directories(sgd-cpp PRIVATE implementations/cpp/src)
target_link_libraries(sgd-cpp PRIVATE serverguard_storage)

add_executable(sg-cpp implementations/cpp/src/cli.cpp)
target_include_directories(sg-cpp PRIVATE implementations/cpp/src)
target_link_libraries(sg-cpp PRIVATE serverguard_storage)

function(sg_test name source)
  add_executable(${name} ${source})
  target_include_directories(${name} PRIVATE implementations/cpp/src)
  add_test(NAME ${name} COMMAND ${name})
  set_tests_properties(${name} PROPERTIES WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})
endfunction()

sg_test(config_contract_test implementations/cpp/tests/config_contract_test.cpp)
sg_test(ssh_auth_contract_test implementations/cpp/tests/ssh_auth_contract_test.cpp)
sg_test(config_validation_test implementations/cpp/tests/config_validation_test.cpp)
sg_test(detector_contract_test implementations/cpp/tests/detector_contract_test.cpp)
sg_test(storage_contract_test implementations/cpp/tests/storage_contract_test.cpp)
target_link_libraries(storage_contract_test PRIVATE serverguard_storage)
sg_test(daemon_contract_test implementations/cpp/tests/daemon_contract_test.cpp)
target_link_libraries(daemon_contract_test PRIVATE serverguard_storage)
sg_test(cli_contract_test implementations/cpp/tests/cli_contract_test.cpp)
target_link_libraries(cli_contract_test PRIVATE serverguard_storage)
