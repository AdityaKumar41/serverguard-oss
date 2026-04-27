#pragma once

#include <set>
#include <stdexcept>
#include <string>

#include "config.hpp"

namespace sg {

inline void require_non_empty(const std::string& value, const std::string& name) {
  if (value.empty()) throw std::runtime_error("invalid config: missing " + name);
}

inline std::set<std::string> validate_sources(const Config& config) {
  std::set<std::string> names;
  if (config.log_sources.empty()) {
    throw std::runtime_error("invalid config: missing log_sources");
  }
  for (const auto& source : config.log_sources) {
    require_non_empty(source.name, "log_sources.name");
    require_non_empty(source.path, "log_sources.path");
    if (source.type != "ssh_auth") {
      throw std::runtime_error("invalid config: unsupported source type");
    }
    if (!names.insert(source.name).second) {
      throw std::runtime_error("invalid config: duplicate log source name");
    }
  }
  return names;
}

inline void validate_detectors(const Config& config,
                               const std::set<std::string>& sources) {
  std::set<std::string> names;
  if (config.detectors.empty()) throw std::runtime_error("invalid config: missing detectors");
  for (const auto& detector : config.detectors) {
    require_non_empty(detector.name, "detectors.name");
    if (detector.name != "ssh_bruteforce") {
      throw std::runtime_error("invalid config: unsupported detector");
    }
    if (!names.insert(detector.name).second) {
      throw std::runtime_error("invalid config: duplicate detector name");
    }
    if (!sources.contains(detector.source)) {
      throw std::runtime_error("invalid config: unknown detector source");
    }
    if (detector.failed_attempt_threshold <= 0) {
      throw std::runtime_error("invalid config: failed_attempt_threshold");
    }
    if (detector.window_seconds <= 0) {
      throw std::runtime_error("invalid config: window_seconds");
    }
  }
}

inline void validate_config(const Config& config) {
  require_non_empty(config.serverguard.instance_id, "serverguard.instance_id");
  require_non_empty(config.serverguard.data_dir, "serverguard.data_dir");
  validate_detectors(config, validate_sources(config));
}

}  // namespace sg

