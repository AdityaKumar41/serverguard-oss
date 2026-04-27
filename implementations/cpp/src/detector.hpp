#pragma once

#include <algorithm>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include "config.hpp"
#include "event.hpp"
#include "ssh_auth.hpp"

namespace sg {

inline int log_second(const std::string& timestamp) {
  return std::stoi(timestamp.substr(7, 2)) * 3600 +
         std::stoi(timestamp.substr(10, 2)) * 60 + std::stoi(timestamp.substr(13, 2));
}

inline std::string metadata_json(const std::vector<SshFailedPasswordAttempt>& attempts,
                                 int window_seconds) {
  std::vector<std::string> lines;
  std::vector<std::string> users;
  std::vector<int> ports;
  for (const auto& attempt : attempts) {
    lines.push_back(attempt.raw_line);
    ports.push_back(attempt.source_port);
    if (std::find(users.begin(), users.end(), attempt.username) == users.end()) {
      users.push_back(attempt.username);
    }
  }
  std::ostringstream out;
  out << "{\"attempt_count\":" << attempts.size()
      << ",\"window_seconds\":" << window_seconds
      << ",\"matched_lines\":" << json_string_array(lines)
      << ",\"usernames\":" << json_string_array(users)
      << ",\"source_ports\":" << json_int_array(ports) << "}";
  return out.str();
}

inline Event make_bruteforce_event(const std::string& source,
                                   const std::vector<SshFailedPasswordAttempt>& attempts,
                                   int window_seconds) {
  return Event{
      .id = unique_id("security-ssh-bruteforce"),
      .timestamp = "2026-04-27T00:00:00Z",
      .type = "security.ssh_bruteforce",
      .severity = "warning",
      .source = source,
      .subject = attempts.front().source_ip,
      .message = "repeated failed SSH login attempts detected",
      .metadata_json = metadata_json(attempts, window_seconds),
  };
}

inline std::vector<Event> detect_ssh_bruteforce(const Config& config,
                                                const std::vector<std::string>& lines) {
  const auto& detector = config.detectors.front();
  const auto& source = config.log_sources.front();
  std::map<std::string, std::vector<SshFailedPasswordAttempt>> by_ip;
  std::vector<Event> events;
  for (const auto& line : lines) {
    const auto parsed = parse_ssh_failed_password(line);
    if (!parsed) continue;
    auto& attempts = by_ip[parsed->source_ip];
    attempts.push_back(*parsed);
    const int cutoff = log_second(parsed->timestamp_text) - detector.window_seconds;
    std::erase_if(attempts, [&](const auto& item) {
      return log_second(item.timestamp_text) < cutoff;
    });
    if (static_cast<int>(attempts.size()) == detector.failed_attempt_threshold) {
      events.push_back(make_bruteforce_event(source.name, attempts, detector.window_seconds));
    }
  }
  return events;
}

}  // namespace sg
