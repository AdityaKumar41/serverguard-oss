#include <cassert>
#include <filesystem>
#include <map>

#include "../src/config.hpp"
#include "../src/runner.hpp"
#include "../src/storage.hpp"

int main() {
  auto config = sg::load_config("fixtures/configs/basic.toml");
  std::filesystem::remove_all(config.serverguard.data_dir);

  sg::run_once(config);
  sg::run_once(config);
  const auto events = sg::EventStore(config.serverguard.data_dir).list_events();
  std::map<std::string, int> counts;
  for (const auto& event : events) ++counts[event.type];

  assert(events.size() == 6);
  assert(counts["audit.daemon_started"] == 2);
  assert(counts["security.ssh_bruteforce"] == 2);
  assert(counts["audit.daemon_stopping"] == 2);
}
