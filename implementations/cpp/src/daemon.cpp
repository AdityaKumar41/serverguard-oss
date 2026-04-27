#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>

#include "config.hpp"
#include "runner.hpp"

namespace {
std::string config_path(int argc, char** argv) {
  for (int i = 1; i + 1 < argc; ++i) {
    if (std::string(argv[i]) == "--config") return argv[i + 1];
  }
  throw std::runtime_error("usage: sgd-cpp --config <path>");
}
}  // namespace

int main(int argc, char** argv) {
  try {
    sg::run_once(sg::load_config(config_path(argc, argv)));
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << "\n";
    return 1;
  }
}

