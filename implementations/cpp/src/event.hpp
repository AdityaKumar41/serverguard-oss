#pragma once

#include <atomic>
#include <chrono>
#include <sstream>
#include <string>
#include <vector>

namespace sg {

struct Event {
  std::string id;
  std::string timestamp;
  std::string type;
  std::string severity;
  std::string source;
  std::string subject;
  std::string message;
  std::string metadata_json;
};

inline std::string unique_id(const std::string& prefix) {
  static std::atomic<int> counter = 0;
  const auto now = std::chrono::system_clock::now().time_since_epoch().count();
  return prefix + "-" + std::to_string(now) + "-" + std::to_string(++counter);
}

inline std::string json_escape(const std::string& value) {
  std::string out;
  for (const char ch : value) {
    if (ch == '"' || ch == '\\') out += '\\';
    if (ch == '\n') {
      out += "\\n";
    } else {
      out += ch;
    }
  }
  return out;
}

inline std::string json_string_array(const std::vector<std::string>& values) {
  std::ostringstream out;
  out << "[";
  for (size_t i = 0; i < values.size(); ++i) {
    if (i) out << ",";
    out << "\"" << json_escape(values[i]) << "\"";
  }
  out << "]";
  return out.str();
}

inline std::string json_int_array(const std::vector<int>& values) {
  std::ostringstream out;
  out << "[";
  for (size_t i = 0; i < values.size(); ++i) {
    if (i) out << ",";
    out << values[i];
  }
  out << "]";
  return out.str();
}

}  // namespace sg
