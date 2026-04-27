#pragma once

#include <optional>
#include <regex>
#include <string>

namespace sg {

struct SshFailedPasswordAttempt {
  std::string timestamp_text;
  std::string username;
  std::string source_ip;
  int source_port = 0;
  std::string raw_line;
};

inline std::optional<SshFailedPasswordAttempt> parse_ssh_failed_password(
    const std::string& line) {
  static const std::regex failed_password(
      R"(^([A-Z][a-z]{2}\s+\d+\s+\d\d:\d\d:\d\d)\s+\S+\s+sshd\[\d+\]:\s+)"
      R"(Failed password for (?:invalid user )?(\S+) from (\S+) port (\d+) ssh2$)");

  std::smatch match;
  // v1 only treats SSH "Failed password" lines as brute-force candidates.
  if (!std::regex_match(line, match, failed_password)) return std::nullopt;

  return SshFailedPasswordAttempt{
      .timestamp_text = match[1].str(),
      .username = match[2].str(),
      .source_ip = match[3].str(),
      .source_port = std::stoi(match[4].str()),
      .raw_line = line,
  };
}

}  // namespace sg
