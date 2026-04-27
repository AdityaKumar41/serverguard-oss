#include <cassert>
#include <filesystem>
#include <string>

#include "../src/cli_commands.hpp"
#include "../src/config.hpp"
#include "../src/runner.hpp"

int main() {
  auto config = sg::load_config("fixtures/configs/basic.toml");
  std::filesystem::remove_all(config.serverguard.data_dir);
  sg::run_once(config);

  const auto status = sg::status_text(config);
  assert(status.find("instance_id: local-dev") != std::string::npos);
  assert(status.find("detectors: 1") != std::string::npos);

  const auto events = sg::events_text(config);
  assert(events.find("security.ssh_bruteforce") != std::string::npos);
  assert(events.find("203.0.113.10") != std::string::npos);
}
