#include <cassert>
#include <filesystem>

#include "../src/event.hpp"
#include "../src/storage.hpp"

int main() {
  const std::filesystem::path dir = "tmp/storage-test";
  std::filesystem::remove_all(dir);

  sg::Event event{
      .id = "test-1",
      .timestamp = "2026-04-27T00:00:00Z",
      .type = "security.ssh_bruteforce",
      .severity = "warning",
      .source = "auth",
      .subject = "203.0.113.10",
      .message = "repeated failed SSH login attempts detected",
      .metadata_json = "{\"attempt_count\":5}",
  };

  sg::EventStore store(dir.string());
  store.insert(event);
  const auto events = store.list_events();

  assert(events.size() == 1);
  assert(events[0].id == "test-1");
  assert(events[0].type == "security.ssh_bruteforce");
  assert(std::filesystem::exists(dir / "serverguard.db"));
}
