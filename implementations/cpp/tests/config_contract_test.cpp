#include <cassert>
#include <string>

#include "../src/config.hpp"

int main() {
  // This test locks the shared fixture contract before parser code exists.
  const auto config = sg::load_config("fixtures/configs/basic.toml");

  assert(config.serverguard.instance_id == "local-dev");
  assert(config.serverguard.data_dir == "./tmp/basic-data");

  assert(config.log_sources.size() == 1);
  assert(config.log_sources[0].name == "auth");
  assert(config.log_sources[0].path == "./fixtures/logs/auth.log");
  assert(config.log_sources[0].type == "ssh_auth");

  assert(config.detectors.size() == 1);
  assert(config.detectors[0].name == "ssh_bruteforce");
  assert(config.detectors[0].enabled);
  assert(config.detectors[0].source == "auth");
  assert(config.detectors[0].failed_attempt_threshold == 5);
  assert(config.detectors[0].window_seconds == 60);
}
