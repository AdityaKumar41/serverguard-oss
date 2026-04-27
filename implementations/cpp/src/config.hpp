#pragma once

#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace sg {
struct ServerGuardConfig {
  std::string instance_id, data_dir;
};
struct LogSourceConfig {
  std::string name, path, type;
};
struct DetectorConfig {
  std::string name;
  bool enabled = false;
  std::string source;
  int failed_attempt_threshold = 0;
  int window_seconds = 0;
};
struct Config {
  ServerGuardConfig serverguard;
  std::vector<LogSourceConfig> log_sources;
  std::vector<DetectorConfig> detectors;
};
inline std::string trim(std::string value) {
  const auto start = value.find_first_not_of(" \t\r\n");
  if (start == std::string::npos) return "";
  const auto end = value.find_last_not_of(" \t\r\n");
  return value.substr(start, end - start + 1);
}
inline std::string unquote(std::string value) {
  value = trim(value);
  if (value.size() >= 2 && value.front() == '"' && value.back() == '"') {
    return value.substr(1, value.size() - 2);
  }
  return value;
}
inline void apply_value(Config& config, const std::string& section,
                        const std::string& key, const std::string& value) {
  if (section == "serverguard") {
    if (key == "instance_id") config.serverguard.instance_id = unquote(value);
    if (key == "data_dir") config.serverguard.data_dir = unquote(value);
    return;
  }
  if (section == "log_sources") {
    auto& source = config.log_sources.back();
    if (key == "name") source.name = unquote(value);
    if (key == "path") source.path = unquote(value);
    if (key == "type") source.type = unquote(value);
    return;
  }
  if (section == "detectors") {
    auto& detector = config.detectors.back();
    if (key == "name") detector.name = unquote(value);
    if (key == "enabled") detector.enabled = trim(value) == "true";
    if (key == "source") detector.source = unquote(value);
    if (key == "failed_attempt_threshold") {
      detector.failed_attempt_threshold = std::stoi(trim(value));
    }
    if (key == "window_seconds") detector.window_seconds = std::stoi(trim(value));
  }
}
inline Config load_config(const std::string& path) {
  std::ifstream file(path);
  if (!file) throw std::runtime_error("missing config file: " + path);
  Config config;
  std::string section;
  std::string line;
  while (std::getline(file, line)) {
    line = trim(line);
    if (line.empty() || line.front() == '#') continue;
    if (line == "[serverguard]") section = "serverguard";
    else if (line == "[[log_sources]]") {
      section = "log_sources";
      config.log_sources.push_back({});
    } else if (line == "[[detectors]]") {
      section = "detectors";
      config.detectors.push_back({});
    } else {
      const auto split = line.find('=');
      if (split == std::string::npos) continue;
      apply_value(config, section, trim(line.substr(0, split)),
                  trim(line.substr(split + 1)));
    }
  }
  return config;
}
}  // namespace sg
