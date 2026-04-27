#include <cassert>
#include <stdexcept>

#include "../src/config.hpp"
#include "../src/config_validate.hpp"

int main() {
  auto config = sg::load_config("fixtures/configs/basic.toml");
  sg::validate_config(config);

  config.serverguard.instance_id = "";
  bool failed = false;
  try {
    sg::validate_config(config);
  } catch (const std::runtime_error& error) {
    failed = std::string(error.what()).find("instance_id") != std::string::npos;
  }
  assert(failed);
}
