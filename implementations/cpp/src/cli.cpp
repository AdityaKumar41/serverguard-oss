#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>

#include "cli_commands.hpp"
#include "config.hpp"

namespace {
std::string config_path(int argc, char** argv) {
  for (int i = 2; i + 1 < argc; ++i) {
    if (std::string(argv[i]) == "--config") return argv[i + 1];
  }
  throw std::runtime_error("usage: sg-cpp <status|events> --config <path>");
}
}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc < 2) throw std::runtime_error("usage: sg-cpp <status|events> --config <path>");
    const auto config = sg::load_config(config_path(argc, argv));
    const std::string command = argv[1];
    if (command == "status") std::cout << sg::status_text(config);
    else if (command == "events") std::cout << sg::events_text(config);
    else throw std::runtime_error("unknown command: " + command);
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << "\n";
    return 1;
  }
}

