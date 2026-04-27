#pragma once

#include <filesystem>
#include <sstream>
#include <string>

#include "config.hpp"
#include "config_validate.hpp"
#include "storage.hpp"

namespace sg {

inline std::string database_path(const Config& config) {
  return (std::filesystem::path(config.serverguard.data_dir) / "serverguard.db").string();
}

inline std::string status_text(const Config& config) {
  validate_config(config);
  std::ostringstream out;
  out << "instance_id: " << config.serverguard.instance_id << "\n";
  out << "data_dir: " << config.serverguard.data_dir << "\n";
  out << "database_path: " << database_path(config) << "\n";
  out << "log_sources: " << config.log_sources.size() << "\n";
  out << "detectors: " << config.detectors.size() << "\n";
  return out.str();
}

inline std::string events_text(const Config& config) {
  validate_config(config);
  std::ostringstream out;
  for (const auto& event : EventStore(config.serverguard.data_dir).list_events()) {
    out << event.timestamp << " " << event.type << " " << event.severity << " "
        << event.source << " " << event.subject << " " << event.message << "\n";
  }
  return out.str();
}

}  // namespace sg

