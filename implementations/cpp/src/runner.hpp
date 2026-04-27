#pragma once

#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "config.hpp"
#include "config_validate.hpp"
#include "detector.hpp"
#include "storage.hpp"

namespace sg {

inline Event audit_event(const Config& config, const std::string& id,
                         const std::string& type, const std::string& message) {
  return Event{
      .id = unique_id(id),
      .timestamp = type == "audit.daemon_started" ? "2026-04-27T00:00:00Z"
                                                  : "2026-04-27T00:00:02Z",
      .type = type,
      .severity = "info",
      .source = "daemon",
      .subject = config.serverguard.instance_id,
      .message = message,
      .metadata_json = "{}",
  };
}

inline std::vector<std::string> read_lines(const std::string& path) {
  std::ifstream file(path);
  if (!file) throw std::runtime_error("missing configured log file: " + path);
  std::vector<std::string> lines;
  for (std::string line; std::getline(file, line);) lines.push_back(line);
  return lines;
}

inline void run_once(const Config& config) {
  validate_config(config);
  EventStore store(config.serverguard.data_dir);
  store.insert(audit_event(config, "audit-started", "audit.daemon_started",
                           "daemon started"));
  for (const auto& event : detect_ssh_bruteforce(config, read_lines(config.log_sources[0].path))) {
    store.insert(event);
  }
  store.insert(audit_event(config, "audit-stopping", "audit.daemon_stopping",
                           "daemon is stopping"));
}

}  // namespace sg
