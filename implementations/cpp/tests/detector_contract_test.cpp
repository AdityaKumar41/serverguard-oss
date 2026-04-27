#include <cassert>
#include <fstream>
#include <string>
#include <vector>

#include "../src/config.hpp"
#include "../src/detector.hpp"

int main() {
  const auto config = sg::load_config("fixtures/configs/basic.toml");
  std::ifstream file(config.log_sources[0].path);
  std::vector<std::string> lines;
  for (std::string line; std::getline(file, line);) lines.push_back(line);

  const auto events = sg::detect_ssh_bruteforce(config, lines);

  assert(events.size() == 1);
  assert(events[0].type == "security.ssh_bruteforce");
  assert(events[0].severity == "warning");
  assert(events[0].source == "auth");
  assert(events[0].subject == "203.0.113.10");
  assert(events[0].metadata_json.find("\"attempt_count\":5") != std::string::npos);
  assert(events[0].metadata_json.find("54325") != std::string::npos);
}
