#include <cassert>
#include <string>

#include "../src/ssh_auth.hpp"

int main() {
  const std::string failed =
      "Apr 25 10:15:01 host sshd[1234]: Failed password for invalid user admin "
      "from 203.0.113.10 port 54321 ssh2";

  const auto attempt = sg::parse_ssh_failed_password(failed);
  assert(attempt.has_value());
  assert(attempt->timestamp_text == "Apr 25 10:15:01");
  assert(attempt->username == "admin");
  assert(attempt->source_ip == "203.0.113.10");
  assert(attempt->source_port == 54321);
  assert(attempt->raw_line == failed);

  const std::string accepted =
      "Apr 25 10:16:05 host sshd[1240]: Accepted publickey for deploy "
      "from 198.51.100.20 port 60211 ssh2";
  assert(!sg::parse_ssh_failed_password(accepted).has_value());
}
